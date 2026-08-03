#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

const NUMBER_PATTERN = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
const WORD_PATTERN = /^[A-Za-z_][A-Za-z0-9_-]*$/;
const RESERVED_WORDS = new Set([
    '+', '-', '*', '/',
    '=', '!=', '>', '>=', '<', '<=',
    'floor', 'dup', 'swap', 'drop',
    'if', 'def', 'end', 'ret', 'store',
    'print', 'dump',
]);

class JorthError extends Error {
    /**
     * @param {string} message
     * @param {{line: number, column: number, text: string} | null} token
     */
    constructor(message, token = null) {
        const location = token === null ? '' : ` at ${token.line}:${token.column}`;
        super(`${message}${location}`);
        this.name = 'JorthError';
    }
}

/**
 * @param {string} source
 * @returns {Array<{text: string, line: number, column: number}>}
 */
function tokenize(source) {
    const tokens = [];
    const lines = source.split(/\r?\n/);

    for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
        const uncommented = lines[lineIndex].split('#', 1)[0];
        const matches = uncommented.matchAll(/\S+/g);

        for (const match of matches) {
            tokens.push({
                text: match[0],
                line: lineIndex + 1,
                column: match.index + 1,
            });
        }
    }

    return tokens;
}

/**
 * @param {string} text
 * @returns {boolean}
 */
function isNumberToken(text) {
    return NUMBER_PATTERN.test(text);
}

/**
 * @param {number} value
 * @returns {string}
 */
function formatNumber(value) {
    if (Object.is(value, -0)) {
        return '0';
    }

    return String(value);
}

/**
 * @param {{text: string, line: number, column: number}} token
 * @returns {void}
 */
function validateWordName(token) {
    if (!WORD_PATTERN.test(token.text) || RESERVED_WORDS.has(token.text)) {
        throw new JorthError(`invalid word name '${token.text}'`, token);
    }
}

/**
 * @param {string} source
 * @returns {{
 *   tokens: Array<{text: string, line: number, column: number}>,
 *   ifFalseJumps: Map<number, number>,
 *   definitionJumps: Map<number, number>,
 *   conditionalEnds: Set<number>,
 *   functionEnds: Set<number>,
 *   functions: Map<string, {start: number, end: number}>
 * }}
 */
function compile(source) {
    const tokens = tokenize(source);
    const ifFalseJumps = new Map();
    const definitionJumps = new Map();
    const conditionalEnds = new Set();
    const functionEnds = new Set();
    const functions = new Map();
    const declaredFunctions = new Set();
    const storeTargets = [];
    const blocks = [];

    for (let index = 0; index < tokens.length; index += 1) {
        const token = tokens[index];

        if (token.text === 'def') {
            if (blocks.length !== 0) {
                throw new JorthError("'def' is only valid at top level", token);
            }

            const nameToken = tokens[index + 1];
            if (nameToken === undefined) {
                throw new JorthError("'def' requires a function name", token);
            }

            validateWordName(nameToken);
            if (declaredFunctions.has(nameToken.text)) {
                throw new JorthError(`duplicate function '${nameToken.text}'`, nameToken);
            }

            declaredFunctions.add(nameToken.text);
            blocks.push({
                kind: 'def',
                index,
                name: nameToken.text,
                bodyStart: index + 2,
                token,
            });
            index += 1;
        } else if (token.text === 'store') {
            const nameToken = tokens[index + 1];
            if (nameToken === undefined) {
                throw new JorthError("'store' requires a variable name", token);
            }

            validateWordName(nameToken);
            storeTargets.push(nameToken);
            index += 1;
        } else if (token.text === 'if') {
            blocks.push({kind: 'if', index, token});
        } else if (token.text === 'ret') {
            const insideFunction = blocks.some((block) => block.kind === 'def');
            if (!insideFunction) {
                throw new JorthError("'ret' is only valid inside a function", token);
            }
        } else if (token.text === 'end') {
            const block = blocks.pop();
            if (block === undefined) {
                throw new JorthError("unmatched 'end'", token);
            }

            if (block.kind === 'if') {
                ifFalseJumps.set(block.index, index + 1);
                conditionalEnds.add(index);
            } else {
                functions.set(block.name, {start: block.bodyStart, end: index});
                definitionJumps.set(block.index, index + 1);
                functionEnds.add(index);
            }
        }
    }

    if (blocks.length !== 0) {
        const block = blocks[blocks.length - 1];
        throw new JorthError(`unclosed '${block.kind}'`, block.token);
    }

    for (const target of storeTargets) {
        if (declaredFunctions.has(target.text)) {
            throw new JorthError(
                `variable '${target.text}' conflicts with a function`,
                target,
            );
        }
    }

    return {
        tokens,
        ifFalseJumps,
        definitionJumps,
        conditionalEnds,
        functionEnds,
        functions,
    };
}

class JorthVM {
    /**
     * @param {{output?: (text: string) => void, maxSteps?: number}} options
     */
    constructor(options = {}) {
        this.output = options.output ?? ((text) => console.log(text));
        this.maxSteps = options.maxSteps ?? 1_000_000;
        this.stack = [];
        this.returnStack = [];
        this.variables = new Map();
    }

    /**
     * @param {string} source
     * @returns {number[]}
     */
    run(source) {
        const program = compile(source);
        this.stack = [];
        this.returnStack = [];
        this.variables = new Map();

        let pc = 0;
        let steps = 0;

        while (pc < program.tokens.length) {
            steps += 1;
            if (steps > this.maxSteps) {
                throw new JorthError(`step limit exceeded (${this.maxSteps})`, program.tokens[pc]);
            }

            const token = program.tokens[pc];
            const word = token.text;

            if (isNumberToken(word)) {
                const value = Number(word);
                this.pushFinite(value, token);
                pc += 1;
                continue;
            }

            if (word === '+') {
                const [left, right] = this.popBinary(token);
                this.pushFinite(left + right, token);
                pc += 1;
            } else if (word === '-') {
                const [left, right] = this.popBinary(token);
                this.pushFinite(left - right, token);
                pc += 1;
            } else if (word === '*') {
                const [left, right] = this.popBinary(token);
                this.pushFinite(left * right, token);
                pc += 1;
            } else if (word === '/') {
                const [left, right] = this.popBinary(token);
                if (right === 0) {
                    throw new JorthError('division by zero', token);
                }
                this.pushFinite(left / right, token);
                pc += 1;
            } else if (word === 'floor') {
                this.pushFinite(Math.floor(this.pop(token)), token);
                pc += 1;
            } else if (word === 'dup') {
                this.requireDepth(1, token);
                this.stack.push(this.stack[this.stack.length - 1]);
                pc += 1;
            } else if (word === 'swap') {
                this.requireDepth(2, token);
                const right = this.stack.pop();
                const left = this.stack.pop();
                this.stack.push(right, left);
                pc += 1;
            } else if (word === 'drop') {
                this.pop(token);
                pc += 1;
            } else if (word === '=') {
                const [left, right] = this.popBinary(token);
                this.stack.push(left === right ? 1 : 0);
                pc += 1;
            } else if (word === '!=') {
                const [left, right] = this.popBinary(token);
                this.stack.push(left !== right ? 1 : 0);
                pc += 1;
            } else if (word === '>') {
                const [left, right] = this.popBinary(token);
                this.stack.push(left > right ? 1 : 0);
                pc += 1;
            } else if (word === '>=') {
                const [left, right] = this.popBinary(token);
                this.stack.push(left >= right ? 1 : 0);
                pc += 1;
            } else if (word === '<') {
                const [left, right] = this.popBinary(token);
                this.stack.push(left < right ? 1 : 0);
                pc += 1;
            } else if (word === '<=') {
                const [left, right] = this.popBinary(token);
                this.stack.push(left <= right ? 1 : 0);
                pc += 1;
            } else if (word === 'if') {
                const condition = this.pop(token);
                const jump = program.ifFalseJumps.get(pc);
                if (jump === undefined) {
                    throw new JorthError("internal error: missing 'if' target", token);
                }
                pc = condition === 0 ? jump : pc + 1;
            } else if (word === 'def') {
                const jump = program.definitionJumps.get(pc);
                if (jump === undefined) {
                    throw new JorthError("internal error: missing 'def' target", token);
                }
                pc = jump;
            } else if (word === 'end') {
                if (program.conditionalEnds.has(pc)) {
                    pc += 1;
                } else if (program.functionEnds.has(pc)) {
                    pc = this.returnFromFunction(token);
                } else {
                    throw new JorthError("internal error: unclassified 'end'", token);
                }
            } else if (word === 'ret') {
                pc = this.returnFromFunction(token);
            } else if (word === 'store') {
                const nameToken = program.tokens[pc + 1];
                if (nameToken === undefined) {
                    throw new JorthError("'store' requires a variable name", token);
                }
                this.variables.set(nameToken.text, this.pop(token));
                pc += 2;
            } else if (word === 'print') {
                this.output(formatNumber(this.pop(token)));
                pc += 1;
            } else if (word === 'dump') {
                this.output(`[${this.stack.map(formatNumber).join(', ')}]`);
                pc += 1;
            } else if (this.variables.has(word)) {
                this.stack.push(this.variables.get(word));
                pc += 1;
            } else if (program.functions.has(word)) {
                const fn = program.functions.get(word);
                this.returnStack.push(pc + 1);
                pc = fn.start;
            } else {
                throw new JorthError(`unknown word '${word}'`, token);
            }
        }

        if (this.returnStack.length !== 0) {
            throw new JorthError('program ended with unfinished function calls');
        }

        return [...this.stack];
    }

    /**
     * @param {{line: number, column: number, text: string}} token
     * @returns {number}
     */
    pop(token) {
        this.requireDepth(1, token);
        return this.stack.pop();
    }

    /**
     * @param {{line: number, column: number, text: string}} token
     * @returns {[number, number]}
     */
    popBinary(token) {
        this.requireDepth(2, token);
        const right = this.stack.pop();
        const left = this.stack.pop();
        return [left, right];
    }

    /**
     * @param {number} depth
     * @param {{line: number, column: number, text: string}} token
     * @returns {void}
     */
    requireDepth(depth, token) {
        if (this.stack.length < depth) {
            throw new JorthError(
                `stack underflow in '${token.text}': need ${depth}, have ${this.stack.length}`,
                token,
            );
        }
    }

    /**
     * @param {number} value
     * @param {{line: number, column: number, text: string}} token
     * @returns {void}
     */
    pushFinite(value, token) {
        if (!Number.isFinite(value)) {
            throw new JorthError(`non-finite numeric result from '${token.text}'`, token);
        }
        this.stack.push(value);
    }

    /**
     * @param {{line: number, column: number, text: string}} token
     * @returns {number}
     */
    returnFromFunction(token) {
        if (this.returnStack.length === 0) {
            throw new JorthError("'ret' is only valid inside a function", token);
        }
        return this.returnStack.pop();
    }
}

/**
 * @param {string[]} argv
 * @returns {number}
 */
function main(argv = process.argv.slice(2)) {
    if (argv.length !== 1) {
        console.error('usage: node jorth.js <filename>');
        return 2;
    }

    const filename = argv[0];
    let source;

    try {
        source = fs.readFileSync(filename, 'utf8');
    } catch (error) {
        console.error(`jorth: cannot read '${filename}': ${error.message}`);
        return 2;
    }

    try {
        new JorthVM().run(source);
        return 0;
    } catch (error) {
        if (error instanceof JorthError) {
            console.error(`jorth: ${error.message}`);
            return 1;
        }
        throw error;
    }
}

if (require.main === module) {
    process.exitCode = main();
}

module.exports = {
    JorthError,
    JorthVM,
    compile,
    tokenize,
};
