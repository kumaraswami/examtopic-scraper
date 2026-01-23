// Global variables
let allQuestions = [];
let currentPage = 1;
let questionsPerPage = 10;
let answeredQuestions = new Set();

// Fetch questions from API when page loads
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/questions');
        allQuestions = await response.json();
        displayQuestions();
    } catch (error) {
        console.error('Error loading questions:', error);
        document.getElementById('questions').innerHTML = 'Error loading questions. Please try again.';
    }
});

function displayQuestions() {
    const startIndex = (currentPage - 1) * questionsPerPage;
    const endIndex = startIndex + questionsPerPage;
    const questionsToShow = allQuestions.slice(startIndex, endIndex);
    
    const questionsDiv = document.getElementById('questions');
    questionsDiv.innerHTML = '';

    questionsToShow.forEach((q, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question';
        const isAnswered = answeredQuestions.has(startIndex + index);
        
        // Remove the word "Question" if it starts with it
        const questionText = q.question.replace(/^Question\s+/i, '');
        
        // Add multi-answer indicator if applicable
        const multiAnswerText = q.is_multi_answer ? 
            '<div style="color: #666; margin-bottom: 5px;">(This question has multiple correct answers)</div>' : '';
        
        questionDiv.innerHTML = `
            <div><strong>Question ${startIndex + index + 1}:</strong></div>
            <div style="margin: 10px 0"><strong>Question:</strong> ${questionText}</div>
            ${multiAnswerText}
            <div class="options">
                ${q.options.map((option, optIndex) => `
                    <div class="option" onclick="selectOption(${startIndex + index}, ${optIndex})">${option}</div>
                `).join('')}
            </div>
            <div class="notes" style="margin-top: 10px; font-style: italic; color: #666; ${isAnswered ? '' : 'display: none;'}">
                ${q.notes}
            </div>
            <button class="clear-button" onclick="clearAnswer(${startIndex + index})" ${isAnswered ? '' : 'style="display: none;"'}>Clear Answer</button>
        `;
        questionsDiv.appendChild(questionDiv);
    });

    updatePagination();
    
    // Update question number input max value
    document.getElementById('questionNumber').max = allQuestions.length;
}

function updatePagination() {
    const totalPages = Math.ceil(allQuestions.length / questionsPerPage);
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
    
    // Update total questions count
    document.querySelector('.instructions').innerHTML = `
        Click on an answer to check if it's correct. The correct answer(s) will be highlighted in green.
        Some questions may have multiple correct answers.
        Use the pagination controls to navigate between questions.<br>
        Total Questions: ${allQuestions.length}
    `;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        displayQuestions();
    }
}

function nextPage() {
    const totalPages = Math.ceil(allQuestions.length / questionsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayQuestions();
    }
}

function changeQuestionsPerPage() {
    questionsPerPage = parseInt(document.getElementById('questionsPerPage').value);
    currentPage = 1;
    displayQuestions();
}

function goToQuestion() {
    const questionNumber = parseInt(document.getElementById('questionNumber').value);
    if (questionNumber && questionNumber > 0 && questionNumber <= allQuestions.length) {
        currentPage = Math.ceil(questionNumber / questionsPerPage);
        displayQuestions();
        
        // Scroll to the specific question
        const questionIndex = (questionNumber - 1) % questionsPerPage;
        const questionElement = document.querySelectorAll('.question')[questionIndex];
        if (questionElement) {
            questionElement.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

function clearAnswer(questionIndex) {
    const options = document.querySelectorAll(`.question:nth-child(${(questionIndex % questionsPerPage) + 1}) .option`);
    const notesDiv = document.querySelectorAll(`.question:nth-child(${(questionIndex % questionsPerPage) + 1}) .notes`)[0];
    const clearButton = document.querySelectorAll(`.question:nth-child(${(questionIndex % questionsPerPage) + 1}) .clear-button`)[0];
    
    options.forEach(opt => {
        opt.classList.remove('selected', 'correct', 'incorrect');
    });

    // Hide community votes and clear button
    notesDiv.style.display = 'none';
    clearButton.style.display = 'none';
    
    // Remove from answered questions
    answeredQuestions.delete(questionIndex);
}

function clearAllAnswers() {
    // Clear all answers from the current page
    const startIndex = (currentPage - 1) * questionsPerPage;
    const endIndex = Math.min(startIndex + questionsPerPage, allQuestions.length);
    
    for (let i = startIndex; i < endIndex; i++) {
        if (answeredQuestions.has(i)) {
            clearAnswer(i);
        }
    }
    
    // Refresh display
    displayQuestions();
}

function selectOption(questionIndex, optionIndex) {
    const question = allQuestions[questionIndex];
    const options = document.querySelectorAll(`.question:nth-child(${(questionIndex % questionsPerPage) + 1}) .option`);
    const notesDiv = document.querySelectorAll(`.question:nth-child(${(questionIndex % questionsPerPage) + 1}) .notes`)[0];
    const clearButton = document.querySelectorAll(`.question:nth-child(${(questionIndex % questionsPerPage) + 1}) .clear-button`)[0];
    
    // Get all correct answers (might be multiple)
    const correctAnswers = question.answer.split('');
    
    options.forEach(opt => {
        opt.classList.remove('selected', 'correct', 'incorrect');
    });

    const selectedOption = options[optionIndex];
    selectedOption.classList.add('selected');

    const selectedAnswer = question.options[optionIndex].charAt(0);
    if (correctAnswers.includes(selectedAnswer)) {
        selectedOption.classList.add('correct');
        // For multi-answer questions, highlight other correct answers
        if (question.is_multi_answer) {
            correctAnswers.forEach(answer => {
                if (answer !== selectedAnswer) {
                    const otherCorrectIndex = question.options.findIndex(opt => opt.charAt(0) === answer);
                    if (otherCorrectIndex !== -1) {
                        options[otherCorrectIndex].classList.add('correct');
                    }
                }
            });
        }
    } else {
        selectedOption.classList.add('incorrect');
        // Highlight all correct answers
        correctAnswers.forEach(answer => {
            const correctOptionIndex = question.options.findIndex(opt => opt.charAt(0) === answer);
            if (correctOptionIndex !== -1) {
                options[correctOptionIndex].classList.add('correct');
            }
        });
    }

    // Show community votes and clear button after answering
    answeredQuestions.add(questionIndex);
    notesDiv.style.display = 'block';
    clearButton.style.display = 'block';
}
