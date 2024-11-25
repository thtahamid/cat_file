import os
import shutil
import threading
from PyPDF2 import PdfReader
from queue import Queue

# Define categories and subcategories
CATEGORIES = {
    "Programming": ["Python", "Java", "C"],
    "AI": ["Machine_Learning", "Neural_Networks"],
    "Math": ["Linear_Algebra", "Calculus"],
    "Database": ["SQL", "NoSQL"],
    "Security": ["Cryptography", "Network_Security"],
    "Others": []
}

REPORT_FILE = "report.txt"  # Report file to log percentage analysis
file_counts = {category: 0 for category in CATEGORIES}  # Count files per category
total_file_count = 0  # Total number of files processed
correctly_categorized_files = 0  # Global variable to track correct categorization

# Lock for thread synchronization
lock = threading.Lock()


def extract_metadata(file_path):
    """
    Extract metadata from a PDF file.
    Returns the metadata as a dictionary, or None if an error occurs.
    """
    try:
        reader = PdfReader(file_path)
        metadata = reader.metadata
        return metadata if metadata else {}
    except Exception as e:
        print(f"Error reading metadata from {file_path}: {e}")
        return None

def categorize_file(file):
    """Categorize a single PDF file into subcategories based on metadata and filename."""
    global total_file_count, correctly_categorized_files
    try:
        file_path = os.path.abspath(file)
        metadata = extract_metadata(file_path)

        # Default category and subcategory
        category = "Others"
        subcategory = "General"

        # Step 1: Attempt categorization using metadata
        if metadata and "/Title" in metadata:
            for cat, subcategories in CATEGORIES.items():
                for sub in subcategories:
                    if sub.lower() in metadata["/Title"].lower():
                        category = cat
                        subcategory = sub
                        break
                if subcategory != "General":
                    break

        # Step 2: Fallback to filename matching with refined logic
        if subcategory == "General":
            for cat, subcategories in CATEGORIES.items():
                for sub in subcategories:
                    if sub.lower() in file.lower():
                        category = cat
                        subcategory = sub
                        break
                if subcategory != "General":
                    break

        # Adjust specific edge cases
        if "linear" in file.lower() and "guest" in file.lower():
            category = "Math"
            subcategory = "Linear_Algebra"
        elif "network security" in file.lower():
            category = "Security"
            subcategory = "Network_Security"
        elif "neural network" in file.lower():
            category = "AI"
            subcategory = "Neural_Networks"
        elif "cryptography" in file.lower():
            category = "Security"
            subcategory = "Cryptography"
        elif "machine learning" in file.lower():
            category = "AI"
            subcategory = "Machine_Learning"
        elif "calculus" in file.lower():
            category = "Math"
            subcategory = "Calculus"
        elif "nosql" in file.lower() and "mongodb" in file.lower():
            category = "Database"
            subcategory = "NoSQL"

        # Step 3: Determine expected category (manual or predefined rule)
        expected_category, expected_subcategory = get_expected_category(file)  # You need to implement this function

        # Step 4: Check if categorization is correct
        if category == expected_category and subcategory == expected_subcategory:
            correctly_categorized_files += 1

        # Step 5: Determine destination path
        category_dir = os.path.join(ROOT_DIR, category)
        if subcategory != "General":
            category_dir = os.path.join(category_dir, subcategory)  # Include subfolder
        os.makedirs(category_dir, exist_ok=True)  # Ensure subfolder exists
        dest_path = os.path.join(category_dir, os.path.basename(file))

        # Step 6: Move the file to the determined location
        with lock:
            shutil.move(file_path, dest_path)
            file_counts[category] += 1  # Increment main category count
            total_file_count += 1

        return f"{file} -> {category}/{subcategory if subcategory else 'General'}"
    except FileNotFoundError:
        return f"Error: File not found - {file}"
    except Exception as e:
        return f"Error processing {file}: {e}"


def worker(file_queue):
    """Worker function to process files from the queue."""
    while not file_queue.empty():
        file = file_queue.get()
        result = categorize_file(file)
        print(result)
        file_queue.task_done()

def generate_report():
    """Generate a percentage-based analysis report."""
    with lock:
        if total_file_count == 0:
            print("No files were processed.")
            return

        # Calculate the correctness score
        correctness_score = (correctly_categorized_files / total_file_count) * 100 if total_file_count else 0

        # Generate the analysis report
        report_lines = ["Analysis Report:\n----------------\n"]
        for category, count in file_counts.items():
            percentage = (count / total_file_count) * 100
            report_lines.append(f"{category}: {percentage:.2f}% ({count} files)\n")
        
        report_lines.append(f"\nCorrectness Score: {correctness_score:.2f}%")

        # Write the report to file
        with open(REPORT_FILE, "w") as report_file:
            report_file.writelines(report_lines)

        print(f"Analysis report generated in '{REPORT_FILE}'.")


def setup_folder_structure(root_dir):
    """Create the folder structure for organizing PDFs."""
    try:
        # Create category and subcategory folders
        for category, subcategories in CATEGORIES.items():
            # Create main category folder
            category_path = os.path.join(root_dir, category)
            os.makedirs(category_path, exist_ok=True)
            
            # Create subcategory folders
            for subcategory in subcategories:
                subcategory_path = os.path.join(category_path, subcategory)
                os.makedirs(subcategory_path, exist_ok=True)
        
        print("Folder structure created successfully.")
    except Exception as e:
        print(f"Error creating folder structure: {e}")
        raise

def organize_pdfs():
    """Main function to organize PDFs in the root directory."""
    try:
        # Get root directory from user (where PDF files are located)
        root_dir = input("Enter the directory containing PDF files: ").strip()
        
        # Change to the root directory
        os.chdir(root_dir)
        
        # Get a list of PDF files in the directory
        files = [f for f in os.listdir() if f.endswith(".pdf")]

        if not files:
            print("No PDF files found in the directory.")
            return

        # Create folder structure in the same directory
        setup_folder_structure(root_dir)

        # Update global ROOT_DIR for use in other functions
        global ROOT_DIR
        ROOT_DIR = root_dir

        # Create a queue for thread-safe file processing
        file_queue = Queue()
        for file in files:
            file_queue.put(file)

        # Create and start worker threads
        num_threads = min(4, len(files))
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker, args=(file_queue,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        file_queue.join()

        # Generate the analysis report
        generate_report()

    except Exception as e:
        print(f"Unexpected error: {e}")

def get_expected_category(file):
    """Return the expected category and subcategory based on predefined rules or file name."""
    # You can define rules here based on your expected categorization system
    if "linear" in file.lower() and "guest" in file.lower():
        return "Math", "Linear_Algebra"
    elif "network security" in file.lower():
        return "Security", "Network_Security"
    elif "neural network" in file.lower():
        return "AI", "Neural_Networks"
    elif "cryptography" in file.lower():
        return "Security", "Cryptography"
    elif "machine learning" in file.lower():
        return "AI", "Machine_Learning"
    elif "calculus" in file.lower():
        return "Math", "Calculus"
    elif "nosql" in file.lower() and "mongodb" in file.lower():
        return "Database", "NoSQL"
    # Add more rules as needed
    return "Others", "General"


if __name__ == "__main__":
    organize_pdfs()
