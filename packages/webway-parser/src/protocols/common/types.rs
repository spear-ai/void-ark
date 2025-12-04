use std::io::Cursor;
use super::{primitives::*, errors::ParseError};

/// Example file metadata structure demonstrating cursor-based parsing
#[derive(Debug, Clone, PartialEq)]
pub struct ExampleFileMetadata {
    /// File size in bytes
    pub file_size: u64,
    /// Creation timestamp (Unix timestamp)
    pub created_at: u32,
    /// File type identifier
    pub file_type: u16,
    /// Compression flag
    pub is_compressed: bool,
    /// Original filename (null-terminated string)
    pub filename: String,
}

/// Parse ExampleFileMetadata from a cursor
/// 
/// Binary layout:
/// - file_size: 8 bytes (u64, little-endian)
/// - created_at: 4 bytes (u32, little-endian) 
/// - file_type: 2 bytes (u16, little-endian)
/// - is_compressed: 1 byte (bool)
/// - filename: null-terminated string
pub fn parse_example_file_metadata(cursor: &mut Cursor<&[u8]>) -> Result<ExampleFileMetadata, ParseError> {
    let file_size = read_u64(cursor)?;
    let created_at = read_u32(cursor)?;
    let file_type = read_u16(cursor)?;
    let is_compressed = read_bool(cursor)?;
    let filename = read_cstring(cursor)?;
    
    Ok(ExampleFileMetadata {
        file_size,
        created_at,
        file_type,
        is_compressed,
        filename,
    })
}

impl ExampleFileMetadata {
    // This contains functions that are not part of the parsing logic
    // but are useful for the application.
    
    // Example:
    // First, parse the data
    // let mut cursor = Cursor::new(data.as_slice());
    // let metadata = parse_example_file_metadata(&mut cursor)?;

    // Then use the helper methods on the parsed instance
    // println!("File type: {}", metadata.file_type_name());  // "Text", "Binary", etc.
    // println!("Is large: {}", metadata.is_large_file());    // true/false

    /// Get the file type as a human-readable string
    pub fn file_type_name(&self) -> &'static str {
        match self.file_type {
            1 => "Text",
            2 => "Binary", 
            3 => "Image",
            4 => "Audio",
            5 => "Video",
            _ => "Unknown",
        }
    }
    
    /// Check if the file is considered large (> 1MB)
    pub fn is_large_file(&self) -> bool {
        self.file_size > 1_048_576 // 1MB
    }
}

