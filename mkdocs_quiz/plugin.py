from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from importlib import resources as impresources
import re
from . import css, js
# import re # Redundant import removed

# Load CSS
inp_file_css = (impresources.files(css) / 'quiz.css')
with inp_file_css.open("rt") as f_css:
    style_content = f_css.read()
style_tag = '<style type="text/css">{}</style>'.format(style_content)

# Load JS
inp_file_js = (impresources.files(js) / 'quiz.js')
with inp_file_js.open("rt") as f_js:
    js_content = f_js.read()
js_tag = '<script type="text/javascript" defer>{}</script>'.format(js_content)


class MkDocsQuizPlugin(BasePlugin):
    def __init__(self):
        self.enabled = True
        self.dirty = False # Not typically used by plugins this way
        self.page_has_quizzes = False # Add this line

    # on_startup is not a standard MkDocs plugin event, removing it.
    # If you need config, use on_config.

    def on_page_markdown(self, markdown, page, config, **kwargs):
        if "quiz" in page.meta and page.meta["quiz"] == "disable":
            return markdown
        self.page_has_quizzes = False # Reset for the current page

        QUIZ_START_TAG = "<?quiz?>"
        QUIZ_END_TAG = "<?/quiz?>"
        # Improved regex to handle potential leading/trailing whitespace within the tags
        REGEX = r'<\?quiz\?>(.*?)<\?/quiz\?>'
        
        # Use a function to process each match to avoid polluting the markdown string in a loop
        # which can lead to issues if quiz tags are nested or if replacement affects subsequent matches.
        # However, for simple sequential replacement, finditer and replacing one by one from end to start
        # or using a temporary list of replacements is safer.
        # For now, let's stick to a slightly safer replacement strategy by collecting replacements.
        
        processed_markdown = markdown
        quiz_id_counter = 0 # To ensure unique IDs for inputs across multiple quizzes on a page

        # Find all matches and process them
        # To safely replace, it's better to iterate and build a new string or replace from the end.
        # For simplicity here, we'll find and replace, but be mindful if quiz content could affect regex.
        
        # Let's find all raw blocks first
        raw_quiz_blocks = re.findall(REGEX, markdown, re.DOTALL)
        
        for match_content in raw_quiz_blocks:
            quiz_lines = match_content.strip().splitlines() # .strip() to remove outer whitespace

            # Ensure there's content to parse
            if not quiz_lines:
                continue

            question_line_index = -1
            content_line_index = -1

            for i, line in enumerate(quiz_lines):
                if line.strip().startswith("question:"):
                    question_line_index = i
                elif line.strip().startswith("content:"):
                    content_line_index = i
                    break # Found content, no need to search further for it

            if question_line_index == -1: # No question found
                # Potentially log a warning or skip this block
                print(f"Warning: Quiz block found without a 'question:': {match_content[:50]}...")
                continue
            
            question = quiz_lines[question_line_index].split("question:", 1)[1].strip()

            # Determine answer lines
            # Answers are between question and content, or question and end if no content
            start_answers_index = question_line_index + 1
            end_answers_index = content_line_index if content_line_index != -1 else len(quiz_lines)
            
            answer_lines_raw = quiz_lines[start_answers_index:end_answers_index]

            parsed_answers = []
            correct_answer_texts = []

            for ans_line in answer_lines_raw:
                ans_line_stripped = ans_line.strip()
                if ans_line_stripped.startswith("answer-correct:"):
                    text = ans_line_stripped.split("answer-correct:", 1)[1].strip()
                    parsed_answers.append({"text": text, "is_correct": True})
                    correct_answer_texts.append(text)
                elif ans_line_stripped.startswith("answer:"):
                    text = ans_line_stripped.split("answer:", 1)[1].strip()
                    parsed_answers.append({"text": text, "is_correct": False})
            
            if not parsed_answers:
                print(f"Warning: Quiz block for question '{question}' has no answers defined.")
                continue

            as_checkboxes = len(correct_answer_texts) > 1
            
            full_answers_html_parts = []
            for i, ans_data in enumerate(parsed_answers):
                input_id = "quiz-{}-{}".format(quiz_id_counter, i)
                input_type = "checkbox" if as_checkboxes else "radio"
                correct_attr = "correct" if ans_data["is_correct"] else ""
                # Use answer text as value for better identification if needed, or keep index
                # Using index as value is simpler for JS if it relies on that.
                # The original JS uses value to match, so let's stick to index `i` for now
                # for minimal JS changes, but this is fragile if order changes.
                # A better value would be a hash of the answer text or the text itself.
                # For now, value="{}" is value="i" as in the original code.
                full_answers_html_parts.append(
                    '<div><input type="{}" name="answer-{}" value="{}" id="{}" {}><label for="{}">{}</label></div>'.format(
                        input_type, quiz_id_counter, i, input_id, correct_attr, input_id, ans_data["text"]
                    )
                )
            
            # Get the content for the explanation section
            explanation_content = ""
            if content_line_index != -1 and (content_line_index + 1) < len(quiz_lines):
                # The line "content:" itself might have text after it or start on new line
                content_start_text = quiz_lines[content_line_index].split("content:",1)[1].strip()
                if content_start_text: # Content starts on the same line
                    explanation_content_lines = [content_start_text] + quiz_lines[content_line_index + 1:]
                else: # Content starts on the next line
                    explanation_content_lines = quiz_lines[content_line_index + 1:]
                explanation_content = "\n".join(explanation_content_lines).strip()

            # --- MODIFIED: Added quiz-score-display div ---
            # --- Also changed name="answer" to be unique per quiz using quiz_id_counter ---
            quiz_html = (
                '<div class="quiz" data-quiz-id="{}">'
                '<h4>Question {}</h4>'
                '<h3>{}</h3>'
                '<form>'
                '<fieldset>{}</fieldset>'
                '<button type="submit" class="quiz-button">Check Answer</button>' # Changed from Submit to Check Answer
                '<div class="quiz-score-display" style="margin-top: 10px; font-weight: bold;">' # Style is optional here
                'Score: <span class="quiz-current-score">0</span> / <span class="quiz-total-possible">1</span>' # Default to 1 point
                '</div>'
                '</form>'
                '<section class="content hidden">{}</section>'
                '</div>'
            ).format(quiz_id_counter, quiz_id_counter + 1, question, "".join(full_answers_html_parts), explanation_content)
            
            # Replace the original block in the markdown
            # This simple replace might be problematic if the match_content is not unique
            # or appears in other contexts. A more robust way is to replace by offsets.
            original_block_to_replace = QUIZ_START_TAG + match_content + QUIZ_END_TAG
            processed_markdown = processed_markdown.replace(original_block_to_replace, quiz_html, 1) # Replace only the first occurrence
            
            quiz_id_counter += 1
        
        if quiz_id_counter > 0:
            self.page_has_quizzes = True # Set the flag if quizzes were processed
            
        return processed_markdown

    def on_page_content(self, html: str, *, page: Page, config: MkDocsConfig, files: Files) -> str | None:
        if self.page_has_quizzes: # Check our flag
            total_score_html = """
            <div id="quiz-total-score-summary" style="margin-top: 20px; padding: 10px; border-top: 1px solid #ccc;">
                <h3>Total Score Summary</h3>
                <p>Your total score for all quizzes on this page is: 
                    <span id="total-quiz-score-achieved">0</span> / 
                    <span id="total-quiz-score-possible">0</span>
                </p>
            </div>
            """
            # Append the summary HTML to the page content
            html += total_score_html

            # Add CSS and JS if quizzes (and thus the summary) are present
            if style_tag not in html:
                html = html + style_tag
            if js_tag not in html:
                html = html + js_tag
        return html
