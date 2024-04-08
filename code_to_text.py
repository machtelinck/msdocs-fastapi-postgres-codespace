import os
import fnmatch


# Dictionary mapping file extensions to their associated programming language
EXTENSION_LANGUAGE = {
    '.py': 'py',
    '.js': 'js',
    '.html': 'html',
    '.css': 'css',
    '.java': 'java',
    '.yml': 'yml',
}


def read_ignore_patterns(ignore_file_path):
    """
    Reads patterns from a file to ignore during file processing.
    
    Args:
        ignore_file_path (str): Path to the file containing ignore patterns.
        
    Returns:
        list: A list of ignore patterns.
    """
    with open(ignore_file_path, 'r') as file:
        # Only non-empty lines are considered and whitespace is stripped
        return [line.strip() for line in file.readlines() if line.strip()]


def is_ignored(path, ignore_patterns, root):
    """
    Determines if a given path matches any of the ignore patterns.
    
    Args:
        path (str): The path to check against ignore patterns.
        ignore_patterns (list): A list of patterns to ignore.
        root (str): The root directory from which relative paths are calculated.
        
    Returns:
        bool: True if the path is ignored, False otherwise.
    """
    for pattern in ignore_patterns:
        # Construct relative path for matching and for folder patterns
        rel_path = os.path.relpath(path, root)
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def read_and_combine_files(input_directory, output_file, ignore_file_path):
    """
    Reads files from a directory, filters them based on ignore patterns,
    and combines them into a single output file with metadata.
    
    Args:
        input_directory (str): The directory to read files from.
        output_file (str): The path to the output file to write combined content.
        ignore_file_path (str): Path to the file containing patterns of files and directories to ignore.
    """
    input_directory = os.path.abspath(input_directory)
    ignore_patterns = read_ignore_patterns(ignore_file_path)

    if not os.path.isdir(input_directory):
        print(f"Specified directory does not exist: {input_directory}")
        return
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(input_directory, topdown=True):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignore_patterns, input_directory)]

            for file in files:
                file_path = os.path.join(root, file)
                if is_ignored(file_path, ignore_patterns, input_directory):
                    continue  # Skip the ignored file
                
                relative_path = os.path.relpath(file_path, input_directory)
                _, extension = os.path.splitext(file)
                language = EXTENSION_LANGUAGE.get(extension, '')

                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        # Write metadata and content to the output file
                        outfile.write(f"---\nPath: {relative_path}\nLanguage: {language}\n---\n")
                        outfile.write(f"```{language}\n")
                        outfile.write(content)
                        outfile.write("\n```\n\n")
                except Exception as e:
                    print(f"Unable to read file {file_path}: {e}")


if __name__ == '__main__':

    project_path = '/workspace/app_django'
    output_file = '/workspace/output.txt'
    ignore_file = '/workspace/ignore_code.txt'

    read_and_combine_files(project_path, output_file, ignore_file)