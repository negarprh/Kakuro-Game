document.addEventListener("DOMContentLoaded", () => {
    // Flow 4 (Play Game): client-side orchestration for input, pause, timer, save, submit.
    const gameCard = document.querySelector(".game-card");
    const inputs = document.querySelectorAll(".cell-input");
    if (!gameCard || !inputs.length) {
        return;
    }

    const submitForm = document.querySelector(".submit-solution-form");
    const pauseButton = document.querySelector("#pauseGameBtn");
    const resumeButton = document.querySelector("#resumeGameBtn");
    const saveGameForm = document.querySelector("#saveGameForm");
    const elapsedDisplay = document.querySelector("#elapsed-time");
    const elapsedInput = document.querySelector("#elapsedTimeInput");
    const submitElapsedInput = document.querySelector("#submitElapsedTimeInput");
    const pauseOverlay = document.querySelector("#pauseOverlay");
    const pauseTarget = document.querySelector("#pauseTarget");
    const isFinished = gameCard.dataset.gameFinished === "1";
    let paused = gameCard.dataset.initialPaused === "1";
    let elapsedSeconds = Number(gameCard.dataset.initialElapsed || "0");
    let timerId = null;
    const dirtyInputs = new Set();

    const formatElapsed = (totalSeconds) => {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    };

    const renderTimer = () => {
        // Flow 4/4E: timer rendering and save payload sync.
        if (elapsedDisplay) {
            elapsedDisplay.textContent = formatElapsed(elapsedSeconds);
        }
        if (elapsedInput) {
            elapsedInput.value = String(elapsedSeconds);
        }
        if (submitElapsedInput) {
            submitElapsedInput.value = String(elapsedSeconds);
        }
    };

    const stopTimer = () => {
        if (timerId !== null) {
            clearInterval(timerId);
            timerId = null;
        }
    };

    const startTimer = () => {
        if (isFinished || paused || timerId !== null) {
            return;
        }
        timerId = window.setInterval(() => {
            elapsedSeconds += 1;
            renderTimer();
        }, 1000);
    };

    const setBoardLocked = (locked) => {
        inputs.forEach((input) => {
            if (!isFinished) {
                input.disabled = locked;
            }
        });

        if (submitForm) {
            const submitButton = submitForm.querySelector("button[type='submit']");
            if (submitButton) {
                submitButton.disabled = locked;
            }
        }
    };

    const applyPausedState = (nextPaused) => {
        // Flow 4E pauseGame/resumeGame: blur/overlay/lock behavior while paused.
        paused = nextPaused;

        if (pauseTarget) {
            pauseTarget.classList.toggle("is-paused", paused);
        }

        if (pauseOverlay) {
            pauseOverlay.classList.toggle("active", paused);
            pauseOverlay.hidden = !paused;
        }

        setBoardLocked(paused);

        if (paused) {
            stopTimer();
        } else {
            startTimer();
        }
    };

    const setErrorMessage = (message) => {
        const statusEl = document.querySelector(".inline-msg.error");
        if (!statusEl) {
            return;
        }
        statusEl.textContent = message;
    };

    const sendPauseAction = async (url) => {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });

        if (!response.ok) {
            return false;
        }

        const data = await response.json();
        if (!data.ok) {
            setErrorMessage(`Move error: ${data.message}`);
            return false;
        }

        return true;
    };

    const sendMove = async (input) => {
        // Flow 4A enterNumber (and Flow 4C removeNumber when value is empty): sync with /game/enter.
        if (paused) {
            return false;
        }

        const row = input.dataset.row;
        const col = input.dataset.col;
        const value = input.value;

        const body = new URLSearchParams({ row, col, value });

        const response = await fetch("/game/enter", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            },
            body,
        });

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        if (!data.ok) {
            input.value = "";
            setErrorMessage(`Move error: ${data.message}`);
            return false;
        }

        setErrorMessage("");

        return true;
    };

    const moveByArrow = (current, key) => {
        const row = Number(current.dataset.row);
        const col = Number(current.dataset.col);

        let nextRow = row;
        let nextCol = col;

        if (key === "ArrowUp") nextRow -= 1;
        if (key === "ArrowDown") nextRow += 1;
        if (key === "ArrowLeft") nextCol -= 1;
        if (key === "ArrowRight") nextCol += 1;

        const next = document.querySelector(`.cell-input[data-row="${nextRow}"][data-col="${nextCol}"]`);
        if (next) {
            next.focus();
            next.select();
        }
    };

    const syncInput = async (input) => {
        if (paused) {
            return false;
        }

        const currentValue = input.value;
        if (!dirtyInputs.has(input) && input.dataset.syncedValue === currentValue) {
            return true;
        }

        const ok = await sendMove(input);
        input.dataset.syncedValue = input.value;
        dirtyInputs.delete(input);
        return ok;
    };

    inputs.forEach((input) => {
        input.dataset.syncedValue = input.value;

        input.addEventListener("input", () => {
            if (paused) {
                return;
            }
            input.value = input.value.replace(/[^1-9]/g, "").slice(0, 1);
            dirtyInputs.add(input);
        });

        input.addEventListener("change", () => {
            if (paused) {
                return;
            }
            void syncInput(input);
        });

        input.addEventListener("keydown", (event) => {
            if (paused) {
                return;
            }
            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
                event.preventDefault();
                moveByArrow(input, event.key);
            }
        });
    });

    if (pauseButton) {
        pauseButton.addEventListener("click", async () => {
            // Flow 4E: pauseGame.
            if (paused || isFinished) {
                return;
            }

            for (const input of inputs) {
                await syncInput(input);
            }

            const ok = await sendPauseAction("/game/pause");
            if (ok) {
                applyPausedState(true);
            }
        });
    }

    if (resumeButton) {
        resumeButton.addEventListener("click", async () => {
            // Flow 4E: resumeGame.
            if (!paused || isFinished) {
                return;
            }

            const ok = await sendPauseAction("/game/resume");
            if (ok) {
                applyPausedState(false);
            }
        });
    }

    if (saveGameForm) {
        saveGameForm.addEventListener("submit", () => {
            // Flow 4F saveGame: send latest elapsed time to backend.
            renderTimer();
        });
    }

    if (submitForm) {
        submitForm.addEventListener("submit", async (event) => {
            // Flow 4D submitBoard: submit after syncing pending edits.
            if (paused) {
                event.preventDefault();
                return;
            }

            if (submitForm.dataset.submitting === "1") {
                return;
            }

            event.preventDefault();
            for (const input of inputs) {
                await syncInput(input);
            }

            submitForm.dataset.submitting = "1";
            submitForm.submit();
        });
    }

    renderTimer();
    applyPausedState(paused);
    if (!paused) {
        startTimer();
    }
});
