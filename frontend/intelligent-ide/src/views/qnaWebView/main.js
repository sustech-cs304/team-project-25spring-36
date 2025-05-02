(function () {
  const vscode = acquireVsCodeApi();

  const quizContainer = document.getElementById('quiz-container');
  const questionContainer = document.getElementById('question-container');
  const answerInput = document.getElementById('answer-input');
  const submitAnswerButton = document.getElementById('submit-answer-button');
  const progressContainer = document.getElementById('progress-container');
  const importButton = document.getElementById('import-button');
  const fileInput = document.getElementById('file-input');

  let questions = [];
  let currentQuestionIndex = 0;
  let correctAnswers = 0;

  importButton.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const content = await file.text();
    questions = parseQuizFile(content);

    if (questions.length > 0) {
      quizContainer.style.display = 'block';
      displayQuestion(0);
    }

    fileInput.value = '';
  });

  function parseQuizFile(content) {
    const lines = content.split('\n');
    const parsedQuestions = [];
    let currentQuestion = null;

    lines.forEach(line => {
      if (line.startsWith('Q:')) {
        if (currentQuestion) {
          parsedQuestions.push(currentQuestion);
        }
        currentQuestion = { question: line.substring(2).trim(), options: [], answer: '' };
      } else if (line.match(/^\d+\./)) {
        currentQuestion.options.push(line.trim());
      } else if (line.startsWith('A:')) {
        currentQuestion.answer = line.substring(2).trim();
      }
    });

    if (currentQuestion) {
      parsedQuestions.push(currentQuestion);
    }

    return parsedQuestions;
  }

  function displayQuestion(index) {
    const question = questions[index];
    questionContainer.innerHTML = `<p>${question.question}</p>`;

    if (question.options.length > 0) {
      question.options.forEach(option => {
        const optionElement = document.createElement('p');
        optionElement.textContent = option;
        questionContainer.appendChild(optionElement);
      });
    }

    progressContainer.textContent = `Question ${index + 1} of ${questions.length}`;
    answerInput.value = '';
  }

  submitAnswerButton.addEventListener('click', () => {
    const userAnswer = answerInput.value.trim();
    const correctAnswer = questions[currentQuestionIndex].answer;

    if (userAnswer === correctAnswer) {
      correctAnswers++;
    }

    currentQuestionIndex++;
    if (currentQuestionIndex < questions.length) {
      displayQuestion(currentQuestionIndex);
    } else {
      displayQuizResult();
    }
  });

  function displayQuizResult() {
    questionContainer.innerHTML = `<p>You answered ${correctAnswers} out of ${questions.length} questions correctly!</p>`;
    answerInput.style.display = 'none';
    submitAnswerButton.style.display = 'none';
    progressContainer.style.display = 'none';
  }

  console.log('Quiz container:', quizContainer);
  console.log('Questions:', questions);
})();