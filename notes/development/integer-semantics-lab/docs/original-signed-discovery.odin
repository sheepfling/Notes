discoverIntegerSigned :: proc($T: typeid) -> bool where intrinsics.type_is_integer(T) {
  // Sign discovery should try using bitflip first,
  // and then fallback on overflow behavior if the bitflip result is unreliable (not all ones)
  zero := T(0)
  one := T(1)
  all_ones := ~(T{})
  all_ones_data := transmute([size_of(zero)]byte)all_ones
  bitwise_not_is_correct := true
  for all_ones_byte in all_ones_data {
    if all_ones_byte != 255 {
      bitwise_not_is_correct = false
      break
    }
  }

  if bitwise_not_is_correct {
    // can rely on bit flip for sign discovery
    return all_ones < 0
  }

  // fallback on underflow behavior
  underflow_value := (zero - one)

  // subtraction should result in a different value than 0
  underflow_not_saturate := (underflow_value != 0)
  if underflow_not_saturate {
    is_signed := underflow_value < zero
    return is_signed
  }

  num_bits: uint = 8 * size_of(zero)
  tmp := (1 << (num_bits - 2)) - 1
  hypothetical_signed_max := T(2 * tmp + 1)
  hypothetical_signed_overflow_value := hypothetical_signed_max + 1

  // addition of a value should result in a different value
  overflow_not_saturate := hypothetical_signed_overflow_value != hypothetical_signed_max

  if overflow_not_saturate {
    is_signed := hypothetical_signed_overflow_value < hypothetical_signed_max
    return is_signed
  }

  // TODO log this - not sure how else to discover signedness
  return false
}
