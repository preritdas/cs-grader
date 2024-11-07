"""
CS Assignment Grading CLI.

This CLI tool provides functionality for grading CS assignments, particularly designed
for handling submissions from Brightspace. It supports both batch processing of submissions
and parallel grading with detailed feedback.

Main Features:
-------------
1. Collect submissions from Brightspace downloads
   - Recursively process multiple directories
   - Handle duplicate files
   - Preserve original filenames

2. Grade submissions with parallel processing
   - Support for both .zip and .java files
   - Multi-threaded grading
   - Detailed feedback in CSV format
   - Thread-safe operations

Usage Examples:
--------------
1. Collect submissions from Brightspace:
   ```bash
   # Collect from two Brightspace download directories into 'students' directory
   python cli.py collect dir1 dir2 students
   ```

2. Grade submissions:
   ```bash
   # Grade with default settings (single thread, 100 points)
   python cli.py grade students requirements.txt

   # Grade with 4 threads and 150 maximum points
   python cli.py grade students requirements.txt --threads 4 --max-points 150
   ```

Output Format:
-------------
The grading process generates a CSV file with the following columns:
1. Student Name
2. Final Score
3. Extra Credit
4. Code Quality Assessment
5. Requirements Analysis
6. Point Deductions
7. Overall Assessment
8. Areas for Improvement

For more information on specific commands, use:
python cli.py [command] --help
"""
# Standard library imports
import os
import sys
import re
import json
import csv
import threading
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

# Type hints
from typing import Optional, List, Dict, Any, NamedTuple, Tuple
from dataclasses import dataclass

# Third-party imports
import typer
from tqdm import tqdm  # Progress bar
from openai import OpenAI  # OpenAI API client
from dotenv import load_dotenv  # Environment variable management

# Logging setup
import logging


# Load environment variables
load_dotenv()

# Configure logging with thread information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="CS Assignment Grading CLI - Process and grade programming assignments with detailed feedback.",
    no_args_is_help=True
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class SubmissionFile:
    """
    Represents a single file in a submission.
    
    Attributes:
        filename (str): Name of the submitted file
        content (str): Content of the file as text
    """
    filename: str
    content: str


@dataclass
class Submission:
    """
    Represents a complete submission with metadata.
    
    Attributes:
        student_name (str): Extracted name of the student
        files: List[SubmissionFile]: List of submitted files
        original_path (Path): Original location of the submission
    """
    student_name: str
    files: List[SubmissionFile]
    original_path: Path


@dataclass
class GradingResult:
    """
    Represents the raw result of grading a submission.
    
    Attributes:
        student_name (str): Name of the student
        final_score (int): Final numerical score
        max_points (int): Maximum possible points
        code_quality (str): Assessment of code quality
        requirements_assessment (List[Dict]): List of requirement evaluations
        point_deductions (List[Dict]): List of point deductions with reasons
        extra_credit (Dict): Extra credit information
        overall_assessment (str): Overall evaluation
        improvement_suggestions (List[str]): Suggested improvements
    """
    student_name: str
    final_score: int
    max_points: int
    code_quality: str
    requirements_assessment: List[Dict[str, Any]]
    point_deductions: List[Dict[str, Any]]
    extra_credit: Dict[str, Any]
    overall_assessment: str
    improvement_suggestions: List[str]


@dataclass
class FormattedResult:
    """
    Represents a grading result formatted for output.
    
    This format is used for CSV output and includes all feedback
    in a human-readable format.
    
    Attributes:
        last_name (str): Student's last name
        first_name (str): Student's first name
        final_score (str): Score as "points/total"
        extra_credit (str): Extra credit with explanation
        code_quality (str): Code quality assessment
        requirements_analysis (str): Detailed requirements feedback
        point_deductions (str): Explanation of deductions
        overall_assessment (str): Overall evaluation
        areas_for_improvement (str): Improvement suggestions
    """
    last_name: str
    first_name: str
    final_score: str
    extra_credit: str
    code_quality: str
    requirements_analysis: str
    point_deductions: str
    overall_assessment: str
    areas_for_improvement: str


class ThreadSafeWriter:
    """
    Thread-safe file writer using a lock.
    
    This class ensures that file writing operations are atomic
    and thread-safe, preventing race conditions when multiple
    threads need to write to the same file.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def write_safely(self, file_path: Path, mode: str, write_func):
        """
        Execute a write function with thread safety.
        
        Args:
            file_path (Path): Path to the file to write
            mode (str): File open mode ('w', 'a', etc.)
            write_func (callable): Function that performs the writing
        """
        with self._lock:
            with open(file_path, mode) as f:
                return write_func(f)


class SubmissionProcessor:
    """
    Handles discovering and processing submission files.
    
    This class is responsible for finding submissions in a directory,
    extracting student information, and processing both zip and Java files.
    All file operations are thread-safe.
    """
    
    def __init__(self):
        self._file_lock = threading.Lock()
    
    @staticmethod
    def extract_student_name(filename: str) -> str:
        """
        Extract student's name from filename.
        
        Args:
            filename (str): Name of the submission file
            
        Returns:
            str: Student's name in "First Last" format
        """
        return Path(filename).stem.replace('_', ' ')
    
    def process_java_file(self, file_path: Path) -> List[SubmissionFile]:
        """
        Process a single Java file with thread safety.
        
        Args:
            file_path (Path): Path to the Java file
            
        Returns:
            List[SubmissionFile]: List containing the processed Java file
        """
        with self._file_lock:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [SubmissionFile(filename=file_path.name, content=content)]
    
    def process_zip_file(self, file_path: Path) -> List[SubmissionFile]:
        """
        Process a zip file containing Java files with thread safety.
        
        Args:
            file_path (Path): Path to the zip file
            
        Returns:
            List[SubmissionFile]: List of Java files from the zip
        """
        files = []
        with self._file_lock:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('.java'):
                        with zip_ref.open(file_info) as f:
                            content = f.read().decode('utf-8')
                            files.append(SubmissionFile(
                                filename=file_info.filename,
                                content=content
                            ))
        return files
    
    def find_submissions(self, directory: Path) -> List[Submission]:
        """
        Find all valid submissions in directory.
        
        Args:
            directory (Path): Directory to search for submissions
            
        Returns:
            List[Submission]: List of found submissions
        """
        submissions = []
        for file_path in directory.glob('*'):
            if not (file_path.suffix in ['.java', '.zip']):
                continue
                
            student_name = self.extract_student_name(file_path.name)
            
            try:
                if file_path.suffix == '.zip':
                    files = self.process_zip_file(file_path)
                else:
                    files = self.process_java_file(file_path)
                
                submissions.append(Submission(
                    student_name=student_name,
                    files=files,
                    original_path=file_path
                ))
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
        
        return submissions


class ResultFormatter:
    """
    Handles formatting grading results for output.
    
    This class converts raw grading results into a human-readable
    format suitable for CSV output.
    """
    
    @staticmethod
    def split_name(full_name: str) -> Tuple[str, str]:
        """
        Split full name into first and last name.
        
        Args:
            full_name (str): Full name of student
            
        Returns:
            Tuple[str, str]: (last_name, first_name)
        """
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""  # Last name only
        return parts[-1], " ".join(parts[:-1])  # Last name, First name(s)
    
    @staticmethod
    def format_requirements(requirements: List[Dict[str, Any]]) -> str:
        """
        Format requirements assessment into a readable string.
        
        Args:
            requirements (List[Dict]): List of requirement assessments
            
        Returns:
            str: Formatted string showing met and unmet requirements
        """
        met_reqs = [req for req in requirements if req['met']]
        unmet_reqs = [req for req in requirements if not req['met']]
        
        result = []
        if met_reqs:
            result.append("Requirements met:\n- " + "\n- ".join(
                f"{req['requirement']}" for req in met_reqs
            ))
        if unmet_reqs:
            result.append("Requirements not met:\n- " + "\n- ".join(
                f"{req['requirement']}: {req['explanation']}" for req in unmet_reqs
            ))
        return "\n\n".join(result)
    
    @classmethod
    def format_result(cls, result: GradingResult) -> FormattedResult:
        """
        Format a grading result for output.
        
        Args:
            result (GradingResult): Raw grading result
            
        Returns:
            FormattedResult: Formatted result ready for output
        """
        # Split student name into first and last
        last_name, first_name = cls.split_name(result.student_name)
        
        # Format point deductions
        deductions_text = "\n".join(
            f"- {d['reason']} (-{d['points']} points)" 
            for d in result.point_deductions
        ) if result.point_deductions else "No points deducted"
        
        # Format extra credit
        extra_credit_text = (
            f"+{result.extra_credit['points']} points: {result.extra_credit['reason']}"
            if result.extra_credit['awarded']
            else "No extra credit awarded"
        )
        
        return FormattedResult(
            last_name=last_name,
            first_name=first_name,
            final_score=f"{result.final_score}/{result.max_points}",
            extra_credit=extra_credit_text,
            code_quality=result.code_quality,
            requirements_analysis=cls.format_requirements(result.requirements_assessment),
            point_deductions=deductions_text,
            overall_assessment=result.overall_assessment,
            areas_for_improvement="\n- " + "\n- ".join(result.improvement_suggestions)
        )


class ResultWriter:
    """
    Handles writing formatted results to CSV.
    
    This class manages the thread-safe writing of grading results
    to a CSV file with proper formatting and headers.
    """
    
    def __init__(self):
        self._writer = ThreadSafeWriter()
    
    def write_results(self, results: List[FormattedResult], output_path: Path) -> None:
        """
        Write formatted results to CSV file with thread safety.
        
        Args:
            results (List[FormattedResult]): List of results to write
            output_path (Path): Path to output CSV file
        """
        if not results:
            logger.warning("No results to write to CSV")
            return
            
        fieldnames = [
            'Last Name',
            'First Name',
            'Final Score',
            'Extra Credit',
            'Code Quality Assessment',
            'Requirements Analysis',
            'Point Deductions',
            'Overall Assessment',
            'Areas for Improvement'
        ]
        
        rows = [
            {
                'Last Name': r.last_name,
                'First Name': r.first_name,
                'Final Score': r.final_score,
                'Extra Credit': r.extra_credit,
                'Code Quality Assessment': r.code_quality,
                'Requirements Analysis': r.requirements_analysis,
                'Point Deductions': r.point_deductions,
                'Overall Assessment': r.overall_assessment,
                'Areas for Improvement': r.areas_for_improvement
            }
            for r in results
        ]
        
        # Sort rows by last name, then first name
        rows.sort(key=lambda x: (x['Last Name'], x['First Name']))
        
        def write_csv(f):
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        self._writer.write_safely(output_path, 'w', write_csv)
        logger.info(f"Results written to {output_path}")


class Grader:
    """
    Coordinates the grading process.
    
    This class handles the core grading logic, including interaction
    with the grading module and error handling.
    """
    
    def __init__(self, guidelines: str, max_points: int):
        """
        Initialize grader with guidelines and maximum points.
        
        Args:
            guidelines (str): Assignment requirements/guidelines
            max_points (int): Maximum possible points
        """
        self.guidelines = guidelines
        self.max_points = max_points
    

    def grade_submission(self, submission: Submission) -> GradingResult:
        """
        Grade a single submission.
        
        Args:
            submission (Submission): Submission to grade
            
        Returns:
            GradingResult: Grading result with feedback
        """
        try:
            from grader import grade_assignment
            
            # Convert submission files to format expected by grader
            files = [(f.filename, f.content) for f in submission.files]
            
            # Grade the submission
            result = grade_assignment(
                files=files,
                guidelines=self.guidelines,
                student_comment="",
                max_points=self.max_points
            )
            
            return GradingResult(
                student_name=submission.student_name,
                final_score=result['final_score'],
                max_points=self.max_points,
                code_quality=result['code_quality'],
                requirements_assessment=result['requirements_assessment'],
                point_deductions=result['point_deductions'],
                extra_credit=result['extra_credit'],
                overall_assessment=result['overall_assessment'],
                improvement_suggestions=result['improvement_suggestions']
            )
            
        except Exception as e:
            logger.error(f"Error grading submission for {submission.student_name}: {str(e)}")
            return GradingResult(
                student_name=submission.student_name,
                final_score=0,
                max_points=self.max_points,
                code_quality="Error during grading",
                requirements_assessment=[],
                point_deductions=[],
                extra_credit={'awarded': False, 'points': 0, 'reason': ''},
                overall_assessment="Failed to grade submission",
                improvement_suggestions=["Please resubmit or contact instructor"]
            )


@app.command()
def collect_btsp(
    brightspace_dirs: List[str] = typer.Argument(
        ...,
        help="List of Brightspace download directories to process",
        show_default=False
    ),
    output_dir: str = typer.Argument(
        ...,
        help="Directory where submissions will be collected",
        show_default=False
    ),
):
    """
    Collect submissions from Brightspace download directories.
    
    This command processes Brightspace download directories and copies submission
    files to a single output directory. It enforces one submission per student
    (taking the latest) and one file per submission (prioritizing .zip over .java).
    
    Example:
        # Collect submissions from two Brightspace directories
        python cli.py collect dir1 dir2 output_dir
    
    The command will:
    1. Recursively scan all input directories
    2. For each student, identify their latest submission
    3. From that submission, take:
       - First .zip file if present
       - Otherwise first .java file
       - Error if neither exists but other files are present
    4. Copy selected files to the output directory
    5. Show progress with a progress bar
    """
    # Convert paths to Path objects
    brightspace_paths = [Path(d) for d in brightspace_dirs]
    output_path = Path(output_dir)
    
    # Validate input directories
    for path in brightspace_paths:
        if not path.is_dir():
            typer.echo(f"Error: {path} is not a valid directory")
            raise typer.Exit(1)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True)
    
    # Dictionary to track latest submission per student
    student_submissions: Dict[str, Tuple[datetime, Path]] = {}
    
    # Regular expression to extract student name and date from directory name
    pattern = re.compile(r'(\d+)-\d+ - (.+) - (.+)')
    
    # Find all submission directories
    for dir_path in brightspace_paths:
        for path in dir_path.iterdir():
            if not path.is_dir() or path.name == 'index.html':
                continue
                
            match = pattern.match(path.name)
            if not match:
                continue
                
            # Extract student name and submission date
            student_name = match.group(2).strip()
            try:
                date_str = match.group(3)
                submission_date = datetime.strptime(date_str, '%b %d, %Y %I%M %p')
            except ValueError:
                logger.error(f"Could not parse date from directory: {path}")
                continue
            
            # Update if this is the latest submission for this student
            if student_name not in student_submissions or submission_date > student_submissions[student_name][0]:
                student_submissions[student_name] = (submission_date, path)
    
    if not student_submissions:
        typer.echo("No valid submissions found.")
        raise typer.Exit(1)
    
    # Process submissions with progress bar
    with tqdm(total=len(student_submissions), desc="Collecting submissions") as progress:
        for student_name, (_, submission_dir) in student_submissions.items():
            try:
                # Look for .zip files first
                zip_files = list(submission_dir.glob('*.zip'))
                java_files = list(submission_dir.glob('*.java'))
                other_files = list(submission_dir.glob('*'))
                
                # Determine which file to copy
                if zip_files:
                    file_to_copy = zip_files[0]  # Take first .zip file
                elif java_files:
                    file_to_copy = java_files[0]  # Take first .java file
                elif other_files:
                    # If there are files but none are .zip or .java, log error
                    logger.error(f"No valid submission file found for {student_name}. "
                               f"Directory contains: {[f.name for f in other_files]}")
                    progress.update(1)
                    continue
                else:
                    logger.error(f"Empty submission directory for {student_name}")
                    progress.update(1)
                    continue
                
                # Copy file to output directory
                dest_path = output_path / file_to_copy.name
                shutil.copy2(file_to_copy, dest_path)
                
            except Exception as e:
                logger.error(f"Error processing submission for {student_name}: {str(e)}")
            
            progress.update(1)
    
    # Count collected files
    collected = len(list(output_path.glob('*')))
    typer.echo(f"\nCollection complete! {collected} files copied to {output_path}")


def analyze_filename(filename: str) -> Tuple[str | None, str | None]:
    """
    Use GPT-4o-mini to analyze a filename and extract the student's name.
    
    Args:
        filename (str): Original filename
        
    Returns:
        Tuple[str | None, str | None]: Extracted first and last name
            None if the name could not be extracted
    """
    prompt = f"""
    Extract the student's first and last name from this filename: {filename}
    
    Common patterns to consider:
    - Names may be separated by underscores or spaces
    - May include assignment numbers (e.g., asg5, hw5)
    - May include additional descriptors (e.g., "part2", "PartB")
    - May be in various formats (e.g., "LastFirst" or "FirstLast")

    If the student's name is clearly not in the filename, use "n/a" for both fields.
    Fix the capitalization and spacing as needed, ex. "john" -> "John"
    
    Return only a JSON object in this format:
    {{"first_name": "string", "last_name": "string"}}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    if response.choices and response.choices[0].message:
        try:
            result = json.loads(response.choices[0].message.content)
            return (
                result["first_name"] if result["first_name"].lower().strip() != "n/a" else None, 
                result["last_name"] if result["last_name"].lower().strip() != "n/a" else None
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing name from filename {filename}: {e}")
            return None, None

    return None, None

@app.command()
def rename(
    submissions_dir: str = typer.Argument(
        ...,
        help="Directory containing student submissions to rename",
        show_default=False
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show planned renames without executing them",
        show_default=True
    )
):
    """
    Rename student submission files to match the expected naming convention.
    
    This command processes a directory of student submissions and renames files
    to follow the First_Last.ext format (e.g., John_Smith.zip). It first shows
    all planned renames and asks for confirmation before executing them.
    
    Example:
        # Rename all submissions in the 'submissions' directory
        python cli.py rename submissions
        
        # Show planned renames without executing them
        python cli.py rename submissions --dry-run
    
    The command will:
    1. Scan the directory for submission files
    2. Use AI to extract student names from filenames
    3. Generate standardized filenames (First_Last.ext)
    4. Show all planned renames
    5. Execute renames after confirmation
    """
    # Convert path to Path object
    submissions_path = Path(submissions_dir)
    
    # Validate input directory
    if not submissions_path.is_dir():
        typer.echo(f"Error: {submissions_dir} is not a valid directory")
        raise typer.Exit(1)
    
    # Dictionary to store rename operations: old_path -> new_path
    rename_operations: Dict[Path, Path] = {}
    
    # Process all files in directory
    error_filenames: list[str] = []
    for file_path in submissions_path.glob('*'):
        if not file_path.is_file() or file_path.name == 'index.html':
            continue
            
        if not (file_path.suffix in ['.java', '.zip']):
            continue
        
        # Extract student name using GPT-4o-mini
        first_name, last_name = analyze_filename(file_path.name)
        
        if first_name and last_name:
            # Generate new filename
            new_name = f"{first_name}_{last_name}{file_path.suffix}"
            new_path = file_path.parent / new_name
            
            # Store rename operation
            rename_operations[file_path] = new_path
        else:
            logger.error(f"Error extracting student name from {file_path.name}")
            error_filenames.append(file_path.name)
    
    if not rename_operations:
        typer.echo("No files to rename.")
        raise typer.Exit(0)
    
    # Show planned renames
    typer.echo("\nPlanned rename operations:")
    for old_path, new_path in rename_operations.items():
        typer.echo(f"{old_path.name} -> {new_path.name}")

    # Show any filenames that couldn't be processed
    if error_filenames:
        typer.echo("\nFilenames that could not be processed:")
        for filename in error_filenames:
            typer.echo(filename)
    
    # If dry run, exit here
    if dry_run:
        typer.echo("\nDry run complete. No files were renamed.")
        raise typer.Exit(0)
    
    # Ask for confirmation
    if not typer.confirm("\nProceed with renaming?"):
        typer.echo("Operation cancelled.")
        raise typer.Exit(0)
    
    # Execute renames
    with tqdm(total=len(rename_operations), desc="Renaming files") as progress:
        for old_path, new_path in rename_operations.items():
            try:
                # Ensure we don't overwrite existing files
                if new_path.exists():
                    counter = 1
                    while new_path.exists():
                        new_name = f"{new_path.stem}_{counter}{new_path.suffix}"
                        new_path = new_path.parent / new_name
                        counter += 1
                
                # Rename file
                old_path.rename(new_path)
                progress.update(1)
            except Exception as e:
                logger.error(f"Error renaming {old_path} to {new_path}: {e}")
                progress.update(1)
    
    typer.echo("\nRename operations completed!")


@app.command()
def grade(
    submissions_dir: str = typer.Argument(
        ...,
        help="Directory containing student submissions (.java or .zip files)",
        show_default=False
    ),
    guidelines_path: str = typer.Argument(
        ...,
        help="Path to the assignment requirements file",
        show_default=False
    ),
    max_points: Optional[int] = typer.Option(
        100,
        help="Maximum points possible for the assignment",
        show_default=True
    ),
    threads: Optional[int] = typer.Option(
        1,
        help="Number of threads to use for parallel grading",
        show_default=True
    ),
    output: Optional[str] = typer.Option(
        None,
        help="Output CSV file path. If not provided, saves as grading_results.csv in the submissions directory",
        show_default=False
    )
):
    """
    Grade all Java assignments in a directory.
    
    This command processes Java submissions (either .java files or .zip files containing
    Java files) and generates a detailed feedback CSV. It supports parallel processing
    for faster grading of large submission sets.
    
    Example:
        # Grade submissions with 4 threads and 150 maximum points
        python cli.py grade submissions requirements.txt --threads 4 --max-points 150
    
    The command will:
    1. Find all Java submissions in the directory
    2. Grade each submission using the provided guidelines
    3. Generate detailed feedback including:
       - Requirements met/unmet
       - Code quality assessment
       - Point deductions with explanations
       - Extra credit
       - Areas for improvement
    4. Save results to a CSV file
    
    The grading process is thread-safe and shows real-time progress.
    """
    # Validate inputs
    submissions_path = Path(submissions_dir)
    if not submissions_path.is_dir():
        typer.echo(f"Error: {submissions_dir} is not a valid directory")
        raise typer.Exit(1)
    
    guidelines_path = Path(guidelines_path)
    if not guidelines_path.is_file():
        typer.echo(f"Error: {guidelines_path} is not a valid file")
        raise typer.Exit(1)
    
    if max_points <= 0:
        typer.echo("Error: max_points must be positive")
        raise typer.Exit(1)
        
    if threads <= 0:
        typer.echo("Error: threads must be positive")
        raise typer.Exit(1)
    
    # Set default output path if not provided
    output_path = Path(output) if output else submissions_path.parent / 'grading_results.csv'
    
    # Read guidelines
    with open(guidelines_path, 'r', encoding='utf-8') as f:
        guidelines = f.read()
    
    # Find all submissions
    typer.echo("Finding submissions...")
    submission_processor = SubmissionProcessor()
    submissions = submission_processor.find_submissions(submissions_path)
    
    if not submissions:
        typer.echo("No valid submissions found.")
        raise typer.Exit(1)
    
    # Create grader and result writer
    grader = Grader(guidelines, max_points)
    writer = ResultWriter()
    
    # Create result queue for thread safety
    result_queue = Queue()
    
    # Create progress bar
    progress_bar = tqdm(total=len(submissions), desc="Grading")
    progress_lock = threading.Lock()
    
    def process_submission(submission: Submission):
        """Process a single submission with progress tracking."""
        try:
            result = grader.grade_submission(submission)
            formatted_result = ResultFormatter.format_result(result)
            result_queue.put(formatted_result)
        except Exception as e:
            logger.error(f"Error processing {submission.student_name}: {str(e)}")
        finally:
            with progress_lock:
                progress_bar.update(1)
    
    # Grade submissions using thread pool
    typer.echo(f"Grading submissions using {threads} threads...")
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit all grading tasks
        futures = [
            executor.submit(process_submission, submission)
            for submission in submissions
        ]
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()  # This ensures we catch any exceptions
    
    # Close progress bar
    progress_bar.close()
    
    # Collect all results from queue
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    
    # Sort results by student name for consistency
    results.sort(key=lambda x: x.last_name)
    
    # Write results
    typer.echo("Writing results...")
    writer.write_results(results, output_path)
    typer.echo(f"Grading completed! Results saved to: {output_path}")


if __name__ == "__main__":
    app()
