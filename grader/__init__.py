"""Module for grading Java assignments."""
import json
import logging
import re
from openai import OpenAI
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_json(text):
    """
    Extract JSON content from a string, ignoring any text before or after the JSON,
    including markdown code block markers.
    
    Args:
    text (str): The string containing JSON content.
    
    Returns:
    str: The extracted JSON string.
    """
    # Remove markdown code block markers if present
    text = re.sub(r'```json\s*|\s*```', '', text)
    
    # Find the JSON object
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    else:
        raise ValueError("No valid JSON found in the response")

def grade_assignment(java_code, guidelines, student_comment, max_points, file_name):
    """
    Grade a Java assignment based on the provided code, guidelines, and student comment.
    
    Args:
    java_code (str): The student's Java code.
    guidelines (str): The assignment guidelines.
    student_comment (str): Any comments provided by the student.
    max_points (int): The maximum number of points for the assignment.
    file_name (str): The name of the Java file.
    
    Returns:
    dict: A dictionary containing the grading results.
    """
    prompt = f"""
    Assignment Guidelines:
    {guidelines}

    Student's Java Code (File name: {file_name}):
    {java_code}

    Student's Comment:
    {student_comment}

    Maximum Points: {max_points}

    Please grade the above Java code based on the given assignment guidelines. Keep in mind that this is likely the first CS class for most of these students, so be forgiving and lenient with deductions. Follow these steps:

    1. Syntax Check:
       - Analyze the code for any syntax errors as if you were a Java compiler.
       - List any syntax errors found, including line numbers and descriptions.
       - Be forgiving of minor syntax errors that don't significantly impact the code's functionality.
       - Consider the file name when evaluating class name consistency.

    2. Compilation Test:
       - Assuming syntax is correct, check if the code would compile successfully.
       - Identify any potential compilation errors, such as undefined variables or type mismatches.
       - Consider partial credit for code that's close to compiling but has minor issues.
       - Ensure the class name matches the file name (excluding the .java extension) for proper compilation.

    3. Logical Error Detection:
       - Analyze the code for logical errors or flaws in the implementation.
       - Identify any discrepancies between the code's logic and the assignment requirements.
       - Focus on major logical errors and be lenient with minor logical inconsistencies.

    4. Runtime Behavior Simulation:
       - Simulate running the program with various inputs.
       - Provide a summary of the runtime behavior in the following format:
         {{
           "status": "success" or "warning" or "error",
           "summary": "A brief summary of the runtime behavior",
           "details": "More detailed explanation of the runtime behavior, including any potential issues or unexpected results"
         }}
       - Be forgiving of extreme edge cases or minor unexpected behaviors that don't detract from assignment requirements.

    5. Requirements Assessment:
       - List all requirements from the assignment guidelines.
       - For each requirement, state whether it is met (true) or not met (false).
       - If a requirement is partially met, mark it as false and explain the partial completion in the explanation.
       - Provide a brief explanation for each requirement's assessment.

    6. Code Quality and Style:
       - Evaluate the code's readability, organization, and adherence to Java best practices.
       - Focus on major style issues and be lenient with minor style inconsistencies.

    7. Point Deductions:
       - Start with {max_points} points.
       - Deduct points sparingly for syntax errors, compilation errors, logical errors, unmet requirements, and poor code quality.
       - Be very forgiving and deduct minimal points for minor issues.
       - Provide a clear reason for each deduction, focusing on learning opportunities rather than punishment.

    8. Extra Credit:
       - Extra credit should only be awarded for exceptional effort that clearly goes beyond the basic requirements of the assignment.
       - Do not award extra credit simply for meeting all requirements or for code that works properly, as this is expected for the assignment.
       - Look for innovative approaches, additional features, or exceptional code quality that demonstrates a deep understanding and significant extra effort.
       - If extra credit is warranted, award up to 5 points and provide a clear explanation of why the work deserves extra credit. Most extra credit should be between 2-3 points, unless the work is truly exceptional.

    9. Final Evaluation:
       - Summarize the overall assessment of the code, highlighting the positive aspects.
       - Provide constructive suggestions for improvement, focusing on the most important areas for growth.

    Format your response as a JSON object with the following structure:
    {{
        "syntax_check": [
            {{"line": number, "error": "string"}}
        ],
        "compilation_test": {{
            "compiles": boolean,
            "errors": [
                "string"
            ]
        }},
        "logical_errors": [
            "string"
        ],
        "runtime_simulation": {{
            "status": "string",
            "summary": "string",
            "details": "string"
        }},
        "requirements_assessment": [
            {{"requirement": "string", "met": boolean, "explanation": "string"}}
        ],
        "code_quality": "string",
        "point_deductions": [
            {{"reason": "string", "points": number}}
        ],
        "extra_credit": {{
            "awarded": boolean,
            "points": number,
            "reason": "string"
        }},
        "final_score": number,
        "overall_assessment": "string",
        "improvement_suggestions": [
            "string"
        ],
        "comment_consideration": "string"
    }}

    Ensure that your response is a valid JSON object, and all values are JSON-parsable and of the correct type.
    """

    response = client.chat.completions.create(
        model="o1-mini",
        messages=[
            {"role": "user", "content": f"You are an experienced Java programming instructor and compiler expert tasked with grading student assignments.\n\n{prompt}"},
        ]
    )
    
    logging.info(f"OpenAI API response: {response}")
    
    if response.choices and response.choices[0].message:
        try:
            json_str = extract_json(response.choices[0].message.content)
            logging.info(f"Extracted JSON string: {json_str}")
            result = json.loads(json_str)
            logging.info(f"Parsed result: {result}")
            return result
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            logging.error(f"Problematic JSON string: {json_str}")
            raise ValueError(f"Invalid JSON in API response: {e}")
        except Exception as e:
            logging.error(f"Error processing API response: {e}")
            raise
    else:
        logging.error("No valid response from OpenAI API")
        raise ValueError("No valid response from OpenAI API")
