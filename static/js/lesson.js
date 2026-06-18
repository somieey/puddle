let currentStep = 1;

function showStep(step) {
    document.querySelectorAll(".lesson-step").forEach(function(section) {
        section.style.display = "none";
    });

    document.getElementById("step-" + step).style.display = "block";
    document.getElementById("step-count").innerText = step;
}

function nextStep() {
    currentStep++;
    showStep(currentStep);
}

function revealTranslation() {
    document.getElementById("translation").style.display = "block";
}

function revealWord(id) {
    const meaning = document.getElementById(id);
    meaning.style.display = "block";
}

function checkBlankAnswer(correctAnswer) {
    const selected = document.querySelector('input[name="blank_answer"]:checked');
    const result = document.getElementById("blank-result");

    if (!selected) {
        result.innerText = "Please choose an answer first.";
        return;
    }

    if (selected.value === correctAnswer) {
        result.innerText = "Correct! 🎉";
        document.getElementById("blank-next-btn").style.display = "inline-block";
    } else {
        result.innerText = "Not quite. Try again 🦫";
    }
}

let selectedWordButton = null;
let matchedCount = 0;

function selectWord(button, word) {

    if (button.disabled) return;

    document.querySelectorAll("[data-meaning]").forEach(btn => {
        if (!btn.disabled) {
            btn.style.border = "";
        }
    });

    selectedWordButton = button;
    button.style.border = "2px solid #5f8a5b";
}

function selectMeaning(button, meaning) {

    if (!selectedWordButton) {
        document.getElementById("match-result").innerText =
            "Choose a word first 🦫";
        return;
    }

    const correctMeaning =
        selectedWordButton.dataset.meaning;

    if (meaning === correctMeaning) {

        selectedWordButton.disabled = true;
        button.disabled = true;

        selectedWordButton.style.background = "#dff3d8";
        button.style.background = "#dff3d8";

        matchedCount++;

        const totalWords =
            document.querySelectorAll("[data-meaning]").length;

        const progress =
            document.getElementById("match-progress");

        if (progress) {
            progress.innerText =
                `Matched ${matchedCount} / ${totalWords}`;
        }

        document.getElementById("match-result").innerText =
            "Correct! 🎉";

        selectedWordButton = null;

        checkAllMatched(totalWords);

    } else {

        selectedWordButton.style.background = "#ffe1e1";
        button.style.background = "#ffe1e1";

        document.getElementById("match-result").innerText =
            "Try again 🦫";

        setTimeout(() => {

            selectedWordButton.style.background = "";
            selectedWordButton.style.border = "";

            button.style.background = "";

            selectedWordButton = null;

        }, 700);
    }
}

function checkAllMatched(totalWords) {

    if (matchedCount === totalWords) {

        document.getElementById("match-result").innerText =
            "All matched! 🎉";

        document.getElementById("match-next-btn").style.display =
            "inline-block";
    }
}

function checkInterestPractice(correctAnswer) {
    const selected = document.querySelector('input[name="interest_answer"]:checked');
    const result = document.getElementById("interest-result");
    const completeBtn = document.getElementById("interest-complete-btn");

    if (!selected) {
        result.innerText = "Please choose an answer first.";
        return;
    }

    if (selected.value === correctAnswer) {
        result.innerText = "Correct! 🎉";
        completeBtn.style.display = "inline-block";
    } else {
        result.innerText = "Not quite. Try again 🦫";
        completeBtn.style.display = "none";
    }
}

let appVoices = [];

function loadVoices() {
    appVoices = window.speechSynthesis.getVoices();
}

window.speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

function speakText(text) {
    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);

    const preferredVoice = appVoices.find(voice =>
        voice.lang === "mr-IN"
    ) || appVoices.find(voice =>
        voice.lang === "hi-IN" && voice.name.toLowerCase().includes("female")
    ) || appVoices.find(voice =>
        voice.lang === "hi-IN"
    ) || appVoices.find(voice =>
        voice.lang.includes("IN")
    );

    if (preferredVoice) {
        speech.voice = preferredVoice;
        speech.lang = preferredVoice.lang;
    } else {
        speech.lang = "hi-IN";
    }

    speech.rate = 0.75;
    speech.pitch = 1.1;

    window.speechSynthesis.speak(speech);
}

window.onload = function() {
    showStep(1);
};