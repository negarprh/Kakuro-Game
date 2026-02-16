document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll(".cell-input");
    if (!inputs.length) {
        return;
    }
    const submitForm = document.querySelector(".submit-solution-form");
    const dirtyInputs = new Set();

    const sendMove = async (input) => {
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
        const statusEl = document.querySelector(".inline-msg.error");

        if (!data.ok) {
            input.value = "";
            if (statusEl) {
                statusEl.textContent = `Move error: ${data.message}`;
            }
            return false;
        }

        if (statusEl && statusEl.textContent.startsWith("Move error:")) {
            statusEl.textContent = "";
        }

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
            input.value = input.value.replace(/[^1-9]/g, "").slice(0, 1);
            dirtyInputs.add(input);
        });

        input.addEventListener("change", () => {
            void syncInput(input);
        });

        input.addEventListener("keydown", (event) => {
            if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
                event.preventDefault();
                moveByArrow(input, event.key);
            }
        });
    });

    if (submitForm) {
        submitForm.addEventListener("submit", async (event) => {
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
});
