const wheel = document.getElementById("fortuneWheel");
const spinButton = document.getElementById("spinButton");
const resultElement = document.getElementById("fortuneResult");
const balanceElement = document.getElementById("fortuneBalance");
const betButtons = document.querySelectorAll(".bet-button");

let selectedBet = null;
let isSpinning = false;
let currentRotation = 0;


/*
 * 9 physical sectors.
 *
 * Each sector = 40 degrees.
 *
 * The angle represents the CENTER of the sector.
 */
const sectorAngles = {
    "0": 20,
    "0.1": 60,
    "0.5": 100,
    "1": 140,
    "1.5": 200,
    "2": 260,
    "3": 340,
};


/*
 * Select bet
 */
betButtons.forEach((button) => {

    button.addEventListener("click", () => {

        if (isSpinning) {
            return;
        }

        betButtons.forEach((item) => {
            item.classList.remove("selected");
        });

        button.classList.add("selected");

        selectedBet = Number(
            button.dataset.bet
        );

        resultElement.innerHTML = `
            <span>
                Selected bet:
                <strong>
                    ${selectedBet.toLocaleString()} AP
                </strong>
            </span>
        `;
    });

});


/*
 * Spin
 */
spinButton.addEventListener("click", async () => {

    if (isSpinning) {
        return;
    }

    if (!selectedBet) {

        resultElement.innerHTML = `
            <strong>
                Choose your bet first.
            </strong>
        `;

        return;
    }


    isSpinning = true;

    spinButton.disabled = true;

    betButtons.forEach((button) => {
        button.disabled = true;
    });


    resultElement.innerHTML = `
        <strong>
            🎡 The wheel is spinning...
        </strong>
    `;


    try {

        /*
         * Get the REAL result from the server.
         */
        const response = await fetch(
            `/api/fortune-wheel/spin?bet_amount=${selectedBet}`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail || "Something went wrong."
            );

        }


        /*
         * Random animation duration:
         *
         * 7,000 - 10,000 ms
         */
        const spinDuration =
            Math.floor(
                Math.random() * 3001
            ) + 7000;


        /*
         * Random number of full rotations.
         */
        const fullRotations =
            Math.floor(
                Math.random() * 5
            ) + 8;


        /*
         * Get target sector.
         */
        const targetAngle =
            sectorAngles[
                String(data.multiplier)
            ];


        if (targetAngle === undefined) {

            throw new Error(
                "Unknown wheel result."
            );

        }


        /*
         * Rotate backwards so that
         * the selected sector stops
         * under the pointer.
         */
        const finalAngle =
            360 - targetAngle;


        currentRotation +=
            fullRotations * 360 +
            finalAngle;


        wheel.style.transition =
            `transform ${spinDuration}ms cubic-bezier(
                0.12,
                0.8,
                0.18,
                1
            )`;


        wheel.style.transform =
            `rotate(${currentRotation}deg)`;


        /*
         * Wait for animation.
         */
        setTimeout(() => {

            showResult(data);

            isSpinning = false;

            spinButton.disabled = false;

            betButtons.forEach((button) => {
                button.disabled = false;
            });

        }, spinDuration);


    } catch (error) {

        resultElement.innerHTML = `
            <strong>
                ❌ ${error.message}
            </strong>
        `;

        isSpinning = false;

        spinButton.disabled = false;

        betButtons.forEach((button) => {
            button.disabled = false;
        });

    }

});


/*
 * Show result
 */
function showResult(data) {

    const multiplier =
        Number(data.multiplier);

    const win =
        Number(data.win);

    const balance =
        Number(data.balance);

    const bet =
        Number(data.bet);


    /*
     * Update balance.
     */
    if (balanceElement) {

        balanceElement.textContent =
            `${balance.toLocaleString()} AP`;

    }


    let message;


    if (multiplier === 0) {

        message = `
            💀 0x
            <span>
                You lost ${bet.toLocaleString()} AP
            </span>
        `;

    } else if (multiplier === 0.1) {

        message = `
            🔻 0.1x
            <span>
                You received ${win.toLocaleString()} AP
            </span>
        `;

    } else if (multiplier === 0.5) {

        message = `
            🔸 0.5x
            <span>
                You received ${win.toLocaleString()} AP
            </span>
        `;

    } else if (multiplier === 1) {

        message = `
            ⚪ 1x
            <span>
                Your bet was returned:
                ${win.toLocaleString()} AP
            </span>
        `;

    } else if (multiplier === 1.5) {

        message = `
            🔴 1.5x
            <span>
                You won ${win.toLocaleString()} AP
            </span>
        `;

    } else if (multiplier === 2) {

        message = `
            🔥 2x
            <span>
                You won ${win.toLocaleString()} AP
            </span>
        `;

    } else if (multiplier === 3) {

        message = `
            🏆 JACKPOT — 3x!
            <span>
                You won ${win.toLocaleString()} AP
            </span>
        `;

    } else {

        message = `
            ${multiplier}x
            <span>
                ${win.toLocaleString()} AP
            </span>
        `;

    }


    resultElement.innerHTML = `
        <strong>
            ${message}
        </strong>

        <span>
            New balance:
            ${balance.toLocaleString()} AP
        </span>
    `;

}
