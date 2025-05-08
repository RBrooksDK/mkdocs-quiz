// Global score tracking
let overallScoreAchieved = 0;
let overallTotalPossible = 0;
const totalScoreAchievedSpan = document.getElementById('total-quiz-score-achieved');
const totalScorePossibleSpan = document.getElementById('total-quiz-score-possible');

// Calculate initial total possible score and update display
const allQuizzesForTotal = document.querySelectorAll('.quiz');
allQuizzesForTotal.forEach(quizInstance => {
    const individualTotalSpan = quizInstance.querySelector('.quiz-total-possible');
    if (individualTotalSpan) {
        overallTotalPossible += parseInt(individualTotalSpan.textContent) || 1;
    } else {
        overallTotalPossible += 1; // Fallback: assume 1 point if not specified
    }
});

if (totalScorePossibleSpan) {
    totalScorePossibleSpan.textContent = overallTotalPossible;
}
if (totalScoreAchievedSpan) {
    totalScoreAchievedSpan.textContent = overallScoreAchieved; // Initial achieved score is 0
}

document.querySelectorAll('.quiz').forEach((quiz) => {
  let form = quiz.querySelector('form');
  let fieldset = form.querySelector('fieldset');
  let quizId = quiz.dataset.quizId; // Get the unique quiz ID

  // Score display elements for this quiz instance
  let scoreDisplayElement = form.querySelector('.quiz-score-display');
  let currentScoreSpan = scoreDisplayElement ? scoreDisplayElement.querySelector('.quiz-current-score') : null;
  let totalPossibleSpan = scoreDisplayElement ? scoreDisplayElement.querySelector('.quiz-total-possible') : null;

  // Initialize score for this quiz instance
  let currentQuizScore = 0;
  // For now, total possible is read from the HTML (defaulted to 1 by Python)
  // We could make this more dynamic later if needed.
  let totalPossibleScore = totalPossibleSpan ? parseInt(totalPossibleSpan.textContent) : 1;


  // Initialize score display if elements exist
  if (currentScoreSpan) {
      currentScoreSpan.textContent = currentQuizScore;
  }
  if (totalPossibleSpan && isNaN(parseInt(totalPossibleSpan.textContent))) { // Ensure it's set if Python didn't
      totalPossibleSpan.textContent = totalPossibleScore;
  }


  form.addEventListener('submit', (event) => {
    event.preventDefault();

    // Prevent re-scoring if already answered correctly
    if (fieldset.hasAttribute('data-answered-correctly')) {
        // console.log("Quiz " + quizId + " has already been answered correctly.");
        // Show existing feedback but don't re-process
        // You might want to disable the button after a correct answer too.
        return; 
    }

    // Use the unique name for inputs for this quiz
    let selectedAnswers = form.querySelectorAll('input[name="answer-' + quizId + '"]:checked');
    let correctMarkedInputs = fieldset.querySelectorAll(
      'input[name="answer-' + quizId + '"][correct]' // Inputs marked as correct by Python
    );
    
    let is_submission_correct = false;
    if (selectedAnswers.length === correctMarkedInputs.length && correctMarkedInputs.length > 0) {
        is_submission_correct = true; // Assume correct until a mismatch is found
        selectedAnswers.forEach(selectedInput => {
            if (!selectedInput.hasAttribute('correct')) {
                is_submission_correct = false;
            }
        });
    } else if (correctMarkedInputs.length === 0 && selectedAnswers.length > 0) {
        // Case: No answer is marked as correct (e.g. "select all that are wrong"),
        // and user selected something. This is incorrect by default for this quiz type.
        is_submission_correct = false;
    } else if (correctMarkedInputs.length > 0 && selectedAnswers.length !== correctMarkedInputs.length) {
        // Case: There are correct answers, but user didn't select the right number of them.
        is_submission_correct = false;
    }


    // Clear previous styling on all options for this quiz
    const allOptionDivs = fieldset.querySelectorAll('div'); // Assuming each input is wrapped in a div
    allOptionDivs.forEach(div => {
        div.classList.remove('correct', 'wrong');
    });
    
    let section = quiz.querySelector('section.content'); // More specific selector

    if (is_submission_correct) {
      if (section) section.classList.remove('hidden');
      
      if (!fieldset.hasAttribute('data-answered-correctly')) {
          currentQuizScore += 1; // Or whatever point value this quiz is worth
          overallScoreAchieved += 1; // Increment overall score
          fieldset.setAttribute('data-answered-correctly', 'true');
          // Optionally disable the button
          let submitButton = form.querySelector('button[type="submit"]');
          if (submitButton) {
              // submitButton.disabled = true;
              // submitButton.textContent = "Answered";
          }
      }
      
      // Mark all selected (which are all correct in this branch)
      selectedAnswers.forEach(selectedInput => {
          selectedInput.parentElement.classList.add('correct');
      });

    } else { // Incorrect submission
      if (section) section.classList.add('hidden'); // Hide explanation on wrong
      
      // Mark selected answers: correct if they are, wrong if they aren't
      selectedAnswers.forEach(selectedInput => {
        if (selectedInput.hasAttribute('correct')) {
          selectedInput.parentElement.classList.add('correct');
        } else {
          selectedInput.parentElement.classList.add('wrong');
        }
      });

      // Also, explicitly show which ones *should* have been selected if they weren't
      correctMarkedInputs.forEach(correctInput => {
        let isSelected = false;
        selectedAnswers.forEach(sel => { if (sel === correctInput) isSelected = true; });
        if (!isSelected) {
            correctInput.parentElement.classList.add('correct'); // Show it as correct (missed)
            // Add a specific style for "missed correct" if desired
        }
      });
    }

    // Update score display
    if (currentScoreSpan) {
      currentScoreSpan.textContent = currentQuizScore;
    }
    // totalPossibleSpan should remain as set initially for this quiz

    // Update total score summary display
    if (totalScoreAchievedSpan) {
        totalScoreAchievedSpan.textContent = overallScoreAchieved;
    }
  });
});
