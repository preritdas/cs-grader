# CS 101 Assignment Grader

Automates the grading process for Java programming assignments. Now powered by **GPT-5** with the new **OpenAI Responses API** and **Structured Outputs** for enhanced accuracy, type safety, and performance. This system conducts multi-step analysis of student code, with syntax checks, compilation tests, and runtime simulation to detect logical errors + edge cases. Provides detailed feedback and assigns scores based on criteria from assignment requirements. Designed specifically for CS 101 (Intro to Computer Science), taught in Java (so we must of course grade it using Python). :)

https://github.com/user-attachments/assets/363d3fba-7961-46ec-8ab3-e31a4a5e7aaf

## 🚀 New in Version 2.0

- **GPT-5 Model**: Upgraded from o1-preview to GPT-5 for better reasoning and code analysis
- **Responses API**: Migrated to OpenAI's new Responses API for improved performance (40-80% faster)
- **Structured Outputs**: Type-safe grading results using Pydantic models
- **Enhanced Reliability**: Automatic fallback to Chat Completions API if needed
- **Better Error Handling**: Explicit refusal detection and validation

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed information about the API migration.

## Key Features

1. **Automated Grading**: Analyzes Java code using GPT-5 and provides a detailed assessment with structured outputs.
2. **Type-Safe Results**: All grading components are validated through Pydantic models for consistency.
3. **Customizable Criteria**: Allows instructors to set specific grading requirements.
4. **Detailed Feedback**: Offers insights on syntax, logic, runtime behavior, and code quality.
5. **Flexible Scoring**: Supports variable maximum points and extra credit.
6. **Batch Processing**: CLI interface for efficient processing of multiple submissions.
7. **Brightspace Integration**: Tools for collecting and organizing submissions from Brightspace.

## How It Works

### 1. Grading Module (`grader/__init__.py`)

The core functionality has been modernized with the Responses API:

- **OpenAI Responses API**: Uses GPT-5 via the new Responses API with structured outputs
- **Pydantic Models**: Strongly typed grading results with automatic validation
- **Intelligent Fallback**: Automatically falls back to Chat Completions API if needed
- **Enhanced Error Handling**: Detects and handles model refusals and validation errors

### 2. Web Interface (`app.py`)

The user interface is built with Streamlit:

- **File Upload**: Allows uploading of Java files and assignment requirement documents
- **Input Fields**: Provides areas for student comments and setting maximum points
- **Result Display**: Presents grading results in an organized, visually appealing manner
- **Interactive Elements**: Uses expandable sections and charts for detailed breakdowns

### 3. CLI Interface (`cli.py`)

The command-line interface provides efficient batch processing capabilities:

- **Submission Collection**: `collect-btsp` command for organizing Brightspace downloads:
  ```bash
  python cli.py collect-btsp dir1 dir2 output_dir
  ```

- **File Standardization**: `rename` command for normalizing submission filenames:
  ```bash
  python cli.py rename submissions_dir
  python cli.py rename submissions_dir --dry-run  # Preview changes
  ```

- **Batch Grading**: `grade` command for parallel processing of submissions:
  ```bash
  python cli.py grade submissions requirements.txt --threads 4 --max-points 150
  ```

### 4. Grading Process

1. **Input Collection**: 
   - Upload Java files (single or zip) containing student code
   - Provide assignment requirements as a text file
   - Optional student comments can be added
   - Set maximum points (default 100, range 10-200)

2. **AI Analysis**: The system sends the code, requirements, and grading criteria to GPT-5 using the Responses API with structured output format.

3. **Result Processing**: Structured response is automatically parsed and validated through Pydantic models.

4. **Display**: 
   - Web UI: Interactive visualizations with gauge charts, pie charts, and detailed breakdowns
   - CLI: CSV output with comprehensive grading results for batch processing

## Structured Output Components

The grading system now uses strongly typed Pydantic models:

- **SyntaxError**: Identifies syntax errors with line numbers
- **CompilationTest**: Assesses compilation status and errors
- **RuntimeSimulation**: Simulates code execution with status tracking
- **RequirementAssessment**: Evaluates requirement fulfillment
- **PointDeduction**: Tracks point deductions with reasons
- **ExtraCredit**: Manages extra credit awards
- **GradingResult**: Complete grading output with all components

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/preritdas/cs-grader.git
   cd cs-grader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. Run the application:
   ```bash
   # Web interface
   streamlit run app.py
   
   # CLI for batch processing
   python cli.py --help
   ```

## Important Considerations for Usage

1. **Model Access**: Ensure your OpenAI API key has access to GPT-5
2. **Structured Outputs**: The new system guarantees type-safe responses but may refuse inappropriate requests
3. **Customization Needs**: Grading criteria and prompts may need adjustment for different assignments
4. **Feedback Review**: Regularly review AI-generated grades to ensure consistency and fairness
5. **Performance**: 
   - Web UI: Improved latency with Responses API caching
   - CLI: Utilize parallel processing for efficient batch grading

## Technical Benefits

- **3% Better Performance**: GPT-5 with Responses API shows improved accuracy on code evaluation tasks
- **40-80% Faster**: Improved cache utilization reduces API response times
- **Type Safety**: Pydantic models eliminate JSON parsing errors
- **Explicit Refusals**: Programmatically detect when the model cannot grade
- **Cleaner Code**: Structured outputs eliminate complex JSON extraction logic

## Future Improvements

1. **Language Expansion**: Extend support to other programming languages beyond Java
2. **Actual Code Execution**: Implement a secure environment to run and test student code directly
3. **Multi-turn Refinement**: Use `previous_response_id` for iterative grading improvements
4. **Built-in Tools**: Leverage web search for plagiarism detection
5. **Stateful Context**: Maintain grading context across multiple submissions
6. **LMS Integration**: Expand Brightspace integration to support other learning management systems

## Documentation

- [Migration Guide](MIGRATION_GUIDE.md) - Details about the Responses API migration
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses) - Official API documentation
- [Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs) - Learn about structured outputs
