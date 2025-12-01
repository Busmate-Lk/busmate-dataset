"""
Enhanced Route Data Quality Checker
===================================

This script identifies suspicious and potentially corrupted bus route data by detecting:

Original checks:
- Repeated words in route names and descriptions  
- Unusual/corrupted characters (encoding issues)
- Long repeating word patterns (3+ repetitions)

Enhanced checks added:
- Improved word repetition detection (catches partial phrases, separated repetitions)
- Excessive spacing (3+ consecutive spaces)  
- Numeric anomalies (very long numbers, malformed patterns)
- Punctuation errors (excessive punctuation marks)
- Suspicious character suffixes (repeated diacritics)
- Obvious text corruption patterns
- Malformed route patterns (improper formatting)
- Text truncation patterns (incomplete words/phrases)

Note: Empty route_through fields are now considered acceptable and won't be flagged.

The enhanced repetition detection now catches complex patterns like:
- "බේස්ලයින් ප ්ලයින් ප ්ලයින්" (repeated partial phrases)
- "වාඩියමංකඩ වාඩියමංකඩ" (direct repetitions)
- "බෙලිඅත්ත හ බෙලිඅත්ත හරහා" (separated word repetitions)
- Multi-word phrase repetitions across punctuation

Usage:
    # Use default paths
    python 06-1-route_mistakes_identfier.py
    
    # Use custom input file
    python 06-1-route_mistakes_identfier.py --input path/to/input.csv
    
    # Use custom input and output directory
    python 06-1-route_mistakes_identfier.py -i input.csv -o output_directory
"""

import pandas as pd
import re
import argparse
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='Enhanced Route Data Quality Checker')
    parser.add_argument('--input', '-i', 
                       default='staging/step-6-normalized_data/unique_routes.csv',
                       help='Input CSV file path (default: staging/step-6-normalized_data/unique_routes.csv)')
    parser.add_argument('--output-dir', '-o',
                       default='staging/step-7-anomaly_identifying',
                       help='Output directory path (default: staging/step-7-anomaly_identifying)')
    return parser.parse_args()

# Parse command line arguments
args = parse_arguments()

# Set up input and output paths
input_file = args.input
output_dir = args.output_dir

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Set output file paths
suspicious_output = os.path.join(output_dir, 'suspicious_routes.csv')
clean_output = os.path.join(output_dir, 'cleaned_routes.csv')

print(f"Input file: {input_file}")
print(f"Output directory: {output_dir}")
print(f"Loading data from: {input_file}")

# Load the CSV
try:
    df = pd.read_csv(input_file)
    print(f"Successfully loaded {len(df)} routes")
except FileNotFoundError:
    print(f"Error: Input file '{input_file}' not found!")
    print("Please check the file path or use --input to specify a different file.")
    exit(1)
except Exception as e:
    print(f"Error loading input file: {e}")
    exit(1)

# Define detection functions
def detect_repeated_words(text):
    if pd.isna(text):
        return False
    
    # Clean the text by removing punctuation and extra spaces for better comparison
    import string
    cleaned_text = text
    # Remove punctuation but keep spaces
    for punct in string.punctuation:
        cleaned_text = cleaned_text.replace(punct, ' ')
    
    words = cleaned_text.split()
    
    # Check for exact consecutive word repetitions
    for i in range(len(words) - 1):
        if words[i] == words[i + 1] and words[i].strip() != '':
            return True
    
    # Check for repeated multi-word phrases (2-4 word combinations)
    for phrase_len in range(2, 5):  # Check 2, 3, 4 word phrases
        for i in range(len(words) - phrase_len * 2 + 1):
            phrase1 = ' '.join(words[i:i + phrase_len])
            # Look for the same phrase appearing later
            for j in range(i + phrase_len, len(words) - phrase_len + 1):
                phrase2 = ' '.join(words[j:j + phrase_len])
                if phrase1 == phrase2 and phrase1.strip() != '':
                    return True
    
    # Special check for patterns like "word1 word2 word1 word2" (separated repetitions)
    for i in range(len(words) - 3):
        for j in range(i + 2, len(words) - 1):
            if (words[i] == words[j] and words[i+1] == words[j+1] and 
                words[i].strip() != '' and len(words[i]) > 2):
                return True
    
    # Check for patterns like "A X A Y" where A is repeated and X,Y are similar
    for i in range(len(words) - 2):
        if (words[i] == words[i+2] and len(words[i]) > 3 and words[i].strip() != ''):
            # Additional check: if the middle words are similar or one contains the other
            if (words[i+1] == words[i+3] or 
                (len(words[i+1]) > 1 and len(words[i+3]) > 1 and 
                 (words[i+1] in words[i+3] or words[i+3] in words[i+1]))):
                return True
            # Also flag if just the main words repeat regardless of middle words
            return True
    
    # Check for repeated word roots (handling Sinhala word variations)
    word_counts = {}
    for word in words:
        if len(word) > 3:  # Only check substantial words
            # Check if this word or a very similar word already exists
            found_similar = False
            for existing_word in word_counts:
                # Check if words are very similar (allowing for minor variations)
                if (word in existing_word or existing_word in word or 
                    (len(word) > 5 and len(existing_word) > 5 and 
                     word[:4] == existing_word[:4])):  # Same first 4 characters
                    word_counts[existing_word] += 1
                    found_similar = True
                    break
            
            if not found_similar:
                word_counts[word] = 1
            
            # If any word appears more than twice, it's suspicious
            if any(count >= 3 for count in word_counts.values()):
                return True
    
    return False

def detect_unusual_chars(text):
    if pd.isna(text):
        return False
    # Extended pattern for encoding errors and corrupted characters
    unusual_pattern = r'[µÃ¢â¬¦Â°àáâãäåæçèéêëìíîï]|[\u0080-\u009F]'
    return bool(re.search(unusual_pattern, text))

def detect_long_repeats(text):
    if pd.isna(text):
        return False
    # Check for same substring repeating consecutively with space
    return bool(re.search(r'(\b\w+\b)\s+\1\s+\1', text))

def detect_partial_words(text):
    if pd.isna(text):
        return False
    # More targeted approach - look for obvious truncation patterns
    partial_patterns = [
        r'\b\w+\s+\w{1,2}\s*$',  # Words followed by 1-2 character fragments at end
        r'[ක-ෆ]+\s[ක-ෆ]{1,2}\s*$',  # Sinhala words followed by 1-2 Sinhala chars
    ]
    
    for pattern in partial_patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_excessive_spaces(text):
    if pd.isna(text):
        return False
    # Check for multiple consecutive spaces (3 or more to avoid false positives)
    return bool(re.search(r'\s{3,}', text))

def detect_mixed_scripts(text):
    if pd.isna(text):
        return False
    # More conservative - only flag obvious encoding issues
    # Look for single non-Sinhala characters isolated in Sinhala text
    suspicious_patterns = [
        r'[ක-ෆ]+\s[a-zA-Z]\s[ක-ෆ]+',  # Single Latin letter between Sinhala words
        r'[ක-ෆ]+[a-zA-Z][ක-ෆ]+',      # Latin letter without spaces between Sinhala
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_numeric_anomalies(text):
    if pd.isna(text):
        return False
    # Only flag clear anomalies
    patterns = [
        r'\b\d{6,}\b',           # Very long number sequences (6+ digits)
        r'\d+[^\s\d\w,-]{2,}'    # Numbers followed by multiple special chars
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_punctuation_errors(text):
    if pd.isna(text):
        return False
    # Much more conservative punctuation checking - only flag obvious errors
    patterns = [
        r'[,]{3,}',              # Multiple commas (3+)
        r'[.]{4,}',              # Multiple periods (4+, allow for ellipsis)  
        r'[-]{4,}',              # Multiple dashes (4+)
        r'[!@#$%^&*+=<>?`~]',    # Clearly foreign punctuation marks
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_empty_or_whitespace_only(text):
    if pd.isna(text) or text.strip() == "":
        return True
    # Only flag if completely empty or just whitespace - don't enforce minimum length
    return False

def detect_suspicious_suffixes(text):
    if pd.isna(text):
        return False
    # Only flag obvious corruption patterns
    suspicious_patterns = [
        r'\w+ි{3,}',             # Multiple ි characters (3+)
        r'\w+්{3,}',             # Multiple ් characters (3+)
        r'\w+ා{3,}',             # Multiple ා characters (3+)
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_inconsistent_formatting(text):
    if pd.isna(text):
        return False
    # More conservative formatting checks
    patterns = [
        r'[0-9][ක-ෆ](?![රහළ])',   # Number directly attached to Sinhala (except common suffixes)
        r'[ක-ෆ][0-9]',            # Sinhala directly attached to number
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_obvious_corruption(text):
    if pd.isna(text):
        return False
    # New function to catch obviously corrupted text patterns
    corruption_patterns = [
        r'(\b[ක-ෆ]+\b)\s+\1\s+\1\s+\1',  # Same word repeated 4+ times
        r'[ක-ෆ]{25,}',                   # Very long unbroken Sinhala sequences (25+ chars)
        r'[ක-ෆ]+[०-९]{3,}',              # Sinhala followed by multiple Devanagari numerals
    ]
    
    for pattern in corruption_patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_malformed_routes(text):
    if pd.isna(text):
        return False
    # Detect clearly malformed route patterns
    malformed_patterns = [
        r'[0-9]+[ක-ෆ]+[0-9]+',            # Numbers sandwiching Sinhala without spaces
        r'[ක-ෆ]+\s+-\s+$',                # Route name ending with " - "
        r'^\s*-\s*[ක-ෆ]+',                # Route name starting with "- "
    ]
    
    for pattern in malformed_patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_truncation_patterns(text):
    if pd.isna(text):
        return False
    # Detect obvious truncation or incomplete text patterns
    truncation_patterns = [
        r'[ක-ෆ]+\.\.\.',                  # Words ending with ellipsis
        r'[ක-ෆ]+\s*\-\s*$',              # Words ending with dash
        r'[ක-ෆ]+\s+[ක-ෆ]$',              # Word followed by single character at end
        r'^\s*[ක-ෆ]\s+[ක-ෆ]+'            # Single character at start followed by words
    ]
    
    for pattern in truncation_patterns:
        if re.search(pattern, text):
            return True
    return False

def detect_suspicious(route_name, route_through):
    reasons = []
    
    # Existing checks
    if detect_repeated_words(route_name):
        reasons.append('Repeated words in route_name')
    
    if detect_repeated_words(route_through):
        reasons.append('Repeated words in route_through')
    
    if detect_unusual_chars(route_name):
        reasons.append('Unusual chars in route_name')
    
    if detect_unusual_chars(route_through):
        reasons.append('Unusual chars in route_through')
    
    if detect_long_repeats(route_name):
        reasons.append('Long repeats in route_name')
    
    if detect_long_repeats(route_through):
        reasons.append('Long repeats in route_through')
    
    # New enhanced checks - adding gradually to avoid false positives
    if detect_excessive_spaces(route_name):
        reasons.append('Excessive spaces in route_name')
    
    if detect_excessive_spaces(route_through):
        reasons.append('Excessive spaces in route_through')
    
    if detect_numeric_anomalies(route_name):
        reasons.append('Numeric anomalies in route_name')
    
    if detect_numeric_anomalies(route_through):
        reasons.append('Numeric anomalies in route_through')
    
    if detect_punctuation_errors(route_name):
        reasons.append('Punctuation errors in route_name')
    
    if detect_punctuation_errors(route_through):
        reasons.append('Punctuation errors in route_through')
    
    if detect_empty_or_whitespace_only(route_name):
        reasons.append('Empty or insufficient route_name')
    
    # Removed check for empty route_through - it's okay to have empty route_through fields
    # if detect_empty_or_whitespace_only(route_through):
    #     reasons.append('Empty or insufficient route_through')
    
    if detect_suspicious_suffixes(route_name):
        reasons.append('Suspicious suffixes in route_name')
    
    if detect_suspicious_suffixes(route_through):
        reasons.append('Suspicious suffixes in route_through')
    
    if detect_obvious_corruption(route_name):
        reasons.append('Obvious corruption in route_name')
    
    if detect_obvious_corruption(route_through):
        reasons.append('Obvious corruption in route_through')
    
    if detect_malformed_routes(route_name):
        reasons.append('Malformed route pattern in route_name')
    
    if detect_malformed_routes(route_through):
        reasons.append('Malformed route pattern in route_through')
    
    if detect_truncation_patterns(route_name):
        reasons.append('Truncation patterns in route_name')
    
    if detect_truncation_patterns(route_through):
        reasons.append('Truncation patterns in route_through')
    
    return reasons

# Apply detection
df['suspicion_reasons'] = df.apply(
    lambda row: detect_suspicious(row['route_name'], row['route_through']), axis=1
)

# Filter suspicious rows
suspicious_df = df[df['suspicion_reasons'].apply(len) > 0].copy()
clean_df = df[df['suspicion_reasons'].apply(len) == 0].copy()

# Save suspicious rows to CSV
suspicious_df.to_csv(suspicious_output, index=False)
clean_df.to_csv(clean_output, index=False)

print(f"\nResults:")
print(f"Total rows: {len(df)}")
print(f"Suspicious rows: {len(suspicious_df)}")
print(f"Clean rows: {len(clean_df)}")
print(f"Improvement: Found {len(suspicious_df) - 240} additional suspicious routes beyond the original detection")
print(f"\nOutput files:")
print(f"Suspicious rows saved to: {suspicious_output}")
print(f"Clean rows saved to: {clean_output}")

# Print summary of issue types found
if len(suspicious_df) > 0:
    print("\nSummary of issues found:")
    all_reasons = []
    for reasons_list in suspicious_df['suspicion_reasons']:
        if isinstance(reasons_list, list):
            all_reasons.extend(reasons_list)
        else:
            # Handle case where reasons might be stored as string
            import ast
            try:
                parsed_reasons = ast.literal_eval(str(reasons_list))
                if isinstance(parsed_reasons, list):
                    all_reasons.extend(parsed_reasons)
            except:
                pass
    
    from collections import Counter
    reason_counts = Counter(all_reasons)
    for reason, count in reason_counts.most_common():
        print(f"  {reason}: {count}")