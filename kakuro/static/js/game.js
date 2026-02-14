document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll(".cell-input");
    if (inputs.length === 0) {
        return;
    }

    const inputByCoord = new Map();
    const tdByCoord = new Map();

    const keyFor = (row, col) => `${row},${col}`;

    inputs.forEach((input) => {
        const row = Number(input.dataset.row);
        const col = Number(input.dataset.col);
        inputByCoord.set(keyFor(row, col), input);
        tdByCoord.set(keyFor(row, col), input.closest(".play-cell"));
    });

    const clearHighlights = () => {
        tdByCoord.forEach((td) => {
            td.classList.remove("active-across", "active-down", "active-cell");
        });
    };

    const highlightRun = (row, col, dr, dc, className) => {
        let r = row - dr;
        let c = col - dc;
        while (inputByCoord.has(keyFor(r, c))) {
            r -= dr;
            c -= dc;
        }

        r += dr;
        c += dc;
        while (inputByCoord.has(keyFor(r, c))) {
            const td = tdByCoord.get(keyFor(r, c));
            if (td) {
                td.classList.add(className);
            }
            r += dr;
            c += dc;
        }
    };

    const highlightCurrentCell = (input) => {
        const row = Number(input.dataset.row);
        const col = Number(input.dataset.col);
        clearHighlights();
        highlightRun(row, col, 0, 1, "active-across");
        highlightRun(row, col, 1, 0, "active-down");
        const td = tdByCoord.get(keyFor(row, col));
        if (td) {
            td.classList.add("active-cell");
        }
    };

    const focusCell = (row, col) => {
        const target = inputByCoord.get(keyFor(row, col));
        if (target) {
            target.focus();
            target.select();
        }
    };

    const rowMinCol = new Map();
    inputByCoord.forEach((_, key) => {
        const [row, col] = key.split(",").map(Number);
        const existing = rowMinCol.get(row);
        if (existing === undefined || col < existing) {
            rowMinCol.set(row, col);
        }
    });

    const moveToNextCell = (input) => {
        const row = Number(input.dataset.row);
        const col = Number(input.dataset.col);
        const right = inputByCoord.get(keyFor(row, col + 1));
        if (right) {
            right.focus();
            return;
        }

        const rowList = [...rowMinCol.keys()].sort((a, b) => a - b);
        for (const rowCandidate of rowList) {
            if (rowCandidate <= row) {
                continue;
            }
            const firstCol = rowMinCol.get(rowCandidate);
            const candidate = inputByCoord.get(keyFor(rowCandidate, firstCol));
            if (candidate) {
                candidate.focus();
                return;
            }
        }
    };

    inputs.forEach((input) => {
        input.addEventListener("input", () => {
            const value = input.value.replace(/[^1-9]/g, "");
            input.value = value.slice(0, 1);
            if (input.value) {
                moveToNextCell(input);
            }
        });

        input.addEventListener("focus", () => {
            highlightCurrentCell(input);
        });

        input.addEventListener("click", () => {
            highlightCurrentCell(input);
        });

        input.addEventListener("keydown", (event) => {
            const row = Number(input.dataset.row);
            const col = Number(input.dataset.col);

            if (event.key === "ArrowUp") {
                event.preventDefault();
                focusCell(row - 1, col);
            }
            if (event.key === "ArrowDown") {
                event.preventDefault();
                focusCell(row + 1, col);
            }
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                focusCell(row, col - 1);
            }
            if (event.key === "ArrowRight") {
                event.preventDefault();
                focusCell(row, col + 1);
            }
            if (event.key === "Backspace" && input.value === "") {
                focusCell(row, col - 1);
            }
        });
    });

    const firstErrorInput = document.querySelector(".play-cell.server-error .cell-input");
    if (firstErrorInput) {
        firstErrorInput.focus();
    } else {
        inputs[0].focus();
    }
});
