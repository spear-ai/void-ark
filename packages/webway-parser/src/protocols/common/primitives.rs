use std::io::{Cursor, Read};
use byteorder::{LittleEndian, ReadBytesExt};
use super::errors::ParseError;

// Signed integer types
pub fn read_i8(cursor: &mut Cursor<&[u8]>) -> Result<i8, ParseError> {
    let mut buf = [0u8; 1];
    cursor.read_exact(&mut buf)?;
    Ok(buf[0] as i8)
}

pub fn read_i16(cursor: &mut Cursor<&[u8]>) -> Result<i16, ParseError> {
    cursor.read_i16::<LittleEndian>().map_err(ParseError::from)
}

pub fn read_i32(cursor: &mut Cursor<&[u8]>) -> Result<i32, ParseError> {
    cursor.read_i32::<LittleEndian>().map_err(ParseError::from)
}

pub fn read_i64(cursor: &mut Cursor<&[u8]>) -> Result<i64, ParseError> {
    cursor.read_i64::<LittleEndian>().map_err(ParseError::from)
}

// Unsigned integer types
pub fn read_u8(cursor: &mut Cursor<&[u8]>) -> Result<u8, ParseError> {
    cursor.read_u8().map_err(ParseError::from)
}

pub fn read_u16(cursor: &mut Cursor<&[u8]>) -> Result<u16, ParseError> {
    cursor.read_u16::<LittleEndian>().map_err(ParseError::from)
}

pub fn read_u32(cursor: &mut Cursor<&[u8]>) -> Result<u32, ParseError> {
    cursor.read_u32::<LittleEndian>().map_err(ParseError::from)
}

pub fn read_u64(cursor: &mut Cursor<&[u8]>) -> Result<u64, ParseError> {
    cursor.read_u64::<LittleEndian>().map_err(ParseError::from)
}

// Floating point types
pub fn read_f32(cursor: &mut Cursor<&[u8]>) -> Result<f32, ParseError> {
    cursor.read_f32::<LittleEndian>().map_err(ParseError::from)
}

pub fn read_f64(cursor: &mut Cursor<&[u8]>) -> Result<f64, ParseError> {
    cursor.read_f64::<LittleEndian>().map_err(ParseError::from)
}

// Character type
pub fn read_char(cursor: &mut Cursor<&[u8]>) -> Result<char, ParseError> {
    let byte = cursor.read_u8()?;
    // For C char, we treat it as ASCII
    if byte > 127 {
        return Err(ParseError::InvalidData("Non-ASCII character".to_string()));
    }
    Ok(byte as char)
}

// Boolean type (C99 _Bool)
pub fn read_bool(cursor: &mut Cursor<&[u8]>) -> Result<bool, ParseError> {
    let byte = cursor.read_u8()?;
    Ok(byte != 0)
}

// Pointer types (size depends on architecture, assuming 64-bit)
pub fn read_ptr(cursor: &mut Cursor<&[u8]>) -> Result<usize, ParseError> {
    let value = cursor.read_u64::<LittleEndian>()?;
    Ok(value as usize)
}

// Size type (size_t, typically usize)
pub fn read_size_t(cursor: &mut Cursor<&[u8]>) -> Result<usize, ParseError> {
    read_ptr(cursor) // Same as pointer on most systems
}

// String reading functions
pub fn read_cstring(cursor: &mut Cursor<&[u8]>) -> Result<String, ParseError> {
    let mut bytes = Vec::new();
    loop {
        let byte = cursor.read_u8()?;
        if byte == 0 {
            break;
        }
        bytes.push(byte);
    }
    
    String::from_utf8(bytes)
        .map_err(|e| ParseError::InvalidData(format!("Invalid UTF-8 in string: {}", e)))
}

pub fn read_fixed_string(cursor: &mut Cursor<&[u8]>, length: usize) -> Result<String, ParseError> {
    let mut bytes = vec![0u8; length];
    cursor.read_exact(&mut bytes)?;
    
    // Find the first null byte or use the entire length
    let actual_length = bytes.iter().position(|&b| b == 0).unwrap_or(length);
    let trimmed_bytes = &bytes[..actual_length];
    
    String::from_utf8(trimmed_bytes.to_vec())
        .map_err(|e| ParseError::InvalidData(format!("Invalid UTF-8 in fixed string: {}", e)))
}

// Array reading functions
pub fn read_bytes(cursor: &mut Cursor<&[u8]>, length: usize) -> Result<Vec<u8>, ParseError> {
    let mut bytes = vec![0u8; length];
    cursor.read_exact(&mut bytes)?;
    Ok(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_read_i32() {
        let data = vec![0x01, 0x02, 0x03, 0x04];
        let mut cursor = Cursor::new(data.as_slice());
        let value = read_i32(&mut cursor).unwrap();
        assert_eq!(value, 0x04030201); // Little endian
        assert_eq!(cursor.position(), 4);
    }

    #[test]
    fn test_read_u8() {
        let data = vec![0xFF, 0x00];
        let mut cursor = Cursor::new(data.as_slice());
        let value = read_u8(&mut cursor).unwrap();
        assert_eq!(value, 255);
        assert_eq!(cursor.position(), 1);
    }

    #[test]
    fn test_read_cstring() {
        let data = b"Hello\0World\0";
        let mut cursor = Cursor::new(data.as_slice());
        let string = read_cstring(&mut cursor).unwrap();
        assert_eq!(string, "Hello");
        assert_eq!(cursor.position(), 6);
    }

    #[test]
    fn test_insufficient_data() {
        let data = vec![0x01, 0x02];
        let mut cursor = Cursor::new(data.as_slice());
        let result = read_i32(&mut cursor);
        assert!(result.is_err());
    }

    #[test]
    fn test_read_bool() {
        let data = vec![0x01, 0x00, 0xFF];
        let mut cursor = Cursor::new(data.as_slice());
        
        let value1 = read_bool(&mut cursor).unwrap();
        let value2 = read_bool(&mut cursor).unwrap();
        let value3 = read_bool(&mut cursor).unwrap();
        
        assert_eq!(value1, true);
        assert_eq!(value2, false);
        assert_eq!(value3, true);
        assert_eq!(cursor.position(), 3);
    }

    #[test]
    fn test_read_fixed_string() {
        let data = b"Hello\0\0\0World";
        let mut cursor = Cursor::new(data.as_slice());
        let string = read_fixed_string(&mut cursor, 8).unwrap();
        assert_eq!(string, "Hello");
        assert_eq!(cursor.position(), 8);
    }
}
