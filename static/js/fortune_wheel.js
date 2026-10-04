document.addEventListener("DOMContentLoaded", () => {
    const wheel = document.getElementById("fortuneWheel");
    const spinButton = document.getElementById("spinButton");
    const resultBox = document.getElementById("fortuneResult");
    const balanceBox = document.getElementById("fortuneBalance");

    const selectedBetLabel =
        document.getElementById("selectedBetLabel");

    const wheelLevelTitle =
        document.getElementById("wheelLevelTitle");

    const wheelLevelSubtitle =
        document.getElementById("wheelLevelSubtitle");

    const betDropdown =
        document.querySelector(".bet-dropdown");

    const betButtons =
        document.querySelectorAll(".bet-button");


    if (!wheel || !spinButton) {
        console.error("Fortune Wheel: required elements not found.");
        return;
    }


    /* =====================================================
       STATE
       ===================================================== */

    let selectedBet = null;
    let currentRotation = 0;
    let isSpinning = false;


    /* =====================================================
       WHEEL CONTENT

       IMPORTANT:
       All wheels use exactly the same physical
       sector indexes: 0 → 11.
       ===================================================== */

    const WHEEL_CONTENT = {

        SAFE: [
            "0x",
            "0.25x",
            "0.5x",
            "0.75x",
            "1x",
            "1.25x",
            "2K",
            "1.5x",
            "4K",
            "2x",
            "3x",
            "222K",
        ],


        RISK: [
            "0x",
            "0.25x",
            "0.75x",
            "1x",
            "1.25x",
            "1.5x",
            "10K",
            "2x",
            "20K",
            "2.5x",
            "5x",
            "555K",
        ],


        HIGH_ROLLER: [
            "0.25x",
            "0.5x",
            "0.75x",
            "1x",
            "1.5x",
            "2x",
            "222K",
            "444K",
            "5x",
            "7.5x",
            "10x",
            "999K",
        ],
    };


    /* =====================================================
       WHEEL INFORMATION
       ===================================================== */

    const WHEEL_INFO = {

        SAFE: {
            title: "🟢 SAFE WHEEL",
            subtitle:
                "Lower bets · Lower risk · Stable rewards",
        },

        RISK: {
            title: "🟠 RISK WHEEL",
            subtitle:
                "Higher bets · Higher risk · Bigger rewards",
        },

        HIGH_ROLLER: {
            title: "🔴 HIGH ROLLER",
            subtitle:
                "Extreme bets · No 0x · Minimum result is 0.25x",
        },
    };


    /* =====================================================
       FORMAT NUMBER
       ===================================================== */

    function formatNumber(number) {
        return new Intl.NumberFormat("en-US").format(number);
    }


    /* =====================================================
       GET WHEEL LEVEL
       ===================================================== */

    function getWheelLevel(bet) {

        if (bet <= 5_000) {
            return "SAFE";
        }

        if (bet <= 50_000) {
            return "RISK";
        }

        return "HIGH_ROLLER";
    }


    /* =====================================================
       UPDATE SECTOR CONTENT
       ===================================================== */

    function updateWheelContent(level) {

        const content = WHEEL_CONTENT[level];

        if (!content) {
            console.error(
                "Unknown wheel level:",
                level,
            );

            return;
        }


        for (let sector = 0; sector < 12; sector++) {

            const element =
                document.getElementById(
                    `sector-${sector}`,
                );


            if (!element) {

                console.error(
                    `Missing wheel sector: sector-${sector}`,
                );

                continue;
            }


            /*
             * Put the correct reward inside
             * the correct physical sector.
             */

            element.innerHTML =
                content[sector];


            /*
             * Force visibility.
             */

            element.style.display = "flex";
            element.style.visibility = "visible";
            element.style.opacity = "1";
        }


        console.log(
            "Fortune Wheel updated:",
            level,
            content,
        );
    }


    /* =====================================================
       UPDATE WHEEL LEVEL
       ===================================================== */

    function updateWheelLevel() {

        const level =
            selectedBet
                ? getWheelLevel(selectedBet)
                : "SAFE";


        const info =
            WHEEL_INFO[level];


        /*
         * Remove old semantic classes.
         */

        wheel.classList.remove(
            "wheel-safe",
            "wheel-risk",
            "wheel-high-roller",
        );


        /*
         * Add current level.
         */

        if (level === "SAFE") {

            wheel.classList.add(
                "wheel-safe",
            );

        } else if (level === "RISK") {

            wheel.classList.add(
                "wheel-risk",
            );

        } else {

            wheel.classList.add(
                "wheel-high-roller",
            );
        }


        wheel.dataset.level =
            level;


        /*
         * Update heading.
         */

        if (!selectedBet) {

            wheelLevelTitle.textContent =
                "🎡 CHOOSE YOUR BET";

            wheelLevelSubtitle.textContent =
                "Your bet determines the wheel";

        } else {

            wheelLevelTitle.textContent =
                info.title;

            wheelLevelSubtitle.textContent =
                info.subtitle;
        }


        /*
         * Update the actual 12 sectors.
         */

        updateWheelContent(level);
    }


    /* =====================================================
       BET SELECTION
       ===================================================== */

    betButtons.forEach((button) => {

        /*
         * Remember initially locked buttons.
         */

        button.dataset.locked =
            button.disabled
                ? "true"
                : "false";


        button.addEventListener(
            "click",
            () => {

                if (isSpinning) {
                    return;
                }


                const bet =
                    Number(
                        button.dataset.bet,
                    );


                if (!Number.isFinite(bet)) {
                    return;
                }


                selectedBet =
                    bet;


                /*
                 * Selected bet label.
                 */

                selectedBetLabel.textContent =
                    `${formatNumber(bet)} AP`;


                /*
                 * Highlight selected button.
                 */

                betButtons.forEach(
                    (item) => {
                        item.classList.remove(
                            "selected",
                        );
                    },
                );


                button.classList.add(
                    "selected",
                );


                /*
                 * Update wheel.
                 */

                updateWheelLevel();


                /*
                 * Reset result.
                 */

                resultBox.textContent =
                    "Ready to spin 🎡";

                resultBox.className =
                    "fortune-result";


                /*
                 * Close dropdown.
                 */

                if (betDropdown) {
                    betDropdown.removeAttribute(
                        "open",
                    );
                }
            },
        );
    });


    /* =====================================================
       SECTOR → ANGLE
       ===================================================== */

    function getSectorTargetAngle(sector) {

        const normalizedSector =
            ((sector % 12) + 12) % 12;


        return (
            360 -
            normalizedSector * 30
        ) % 360;
    }


    /* =====================================================
       RANDOM FULL ROTATIONS
       ===================================================== */

    function getRandomSpinRounds() {
        return (
            Math.floor(
                Math.random() * 11,
            ) + 5
        );
    }


    /* =====================================================
       RANDOM SPIN DURATION
       ===================================================== */

    function getSpinDuration() {

        return (
            Math.floor(
                Math.random() * 3001,
            ) + 7000
        );
    }


    /* =====================================================
       NORMALIZE ANGLE
       ===================================================== */

    function normalizeAngle(angle) {

        return (
            (angle % 360) + 360
        ) % 360;
    }


    /* =====================================================
       CALCULATE TARGET ROTATION

       Important:
       fixes the old accumulated rotation bug.
       ===================================================== */

    function calculateTargetRotation(sector) {

        const desiredAngle =
            getSectorTargetAngle(
                sector,
            );


        const currentAngle =
            normalizeAngle(
                currentRotation,
            );


        let delta =
            desiredAngle -
            currentAngle;


        if (delta <= 0) {
            delta += 360;
        }


        const rounds =
            getRandomSpinRounds();


        return (
            currentRotation +
            rounds * 360 +
            delta
        );
    }


    /* =====================================================
       ANIMATE WHEEL
       ===================================================== */

    function animateWheel(
        targetRotation,
        duration,
    ) {

        return new Promise(
            (resolve) => {

                wheel.style.transition =
                    `transform ${duration}ms ` +
                    `cubic-bezier(0.12, 0.75, 0.18, 1)`;


                wheel.style.transform =
                    `rotate(${targetRotation}deg)`;


                setTimeout(
                    resolve,
                    duration,
                );
            },
        );
    }


    /* =====================================================
       SPIN
       ===================================================== */

    async function spinWheel() {

        if (isSpinning) {
            return;
        }


        if (!selectedBet) {

            resultBox.textContent =
                "Choose your bet first.";

            resultBox.className =
                "fortune-result error";

            return;
        }


        isSpinning = true;


        spinButton.disabled =
            true;


        betButtons.forEach(
            (button) => {
                button.disabled =
                    true;
            },
        );


        resultBox.textContent =
            "🎡 The wheel is spinning...";

        resultBox.className =
            "fortune-result spinning";


        try {

            const response =
                await fetch(
                    `/api/fortune-wheel/spin?bet_amount=${selectedBet}`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },
                    },
                );


            let data = {};


            try {

                data =
                    await response.json();

            } catch {

                data = {};
            }


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Something went wrong.",
                );
            }


            const sector =
                Number(data.sector);


            if (
                !Number.isInteger(sector) ||
                sector < 0 ||
                sector > 11
            ) {

                throw new Error(
                    "Invalid wheel sector returned by server.",
                );
            }


            /*
             * Calculate final rotation.
             */

            const targetRotation =
                calculateTargetRotation(
                    sector,
                );


            /*
             * 7–10 seconds.
             */

            const duration =
                getSpinDuration();


            await animateWheel(
                targetRotation,
                duration,
            );


            /*
             * Save current rotation.
             */

            currentRotation =
                targetRotation;


            /*
             * Show result.
             */

            showResult(data);


        } catch (error) {

            console.error(
                "Fortune Wheel error:",
                error,
            );


            resultBox.textContent =
                error.message ||
                "Unable to spin the wheel.";

            resultBox.className =
                "fortune-result error";


        } finally {

            isSpinning =
                false;


            spinButton.disabled =
                false;


            /*
             * Restore original locked bets.
             */

            betButtons.forEach(
                (button) => {

                    button.disabled =
                        button.dataset.locked ===
                        "true";
                },
            );
        }
    }


    /* =====================================================
       SHOW RESULT
       ===================================================== */

    function showResult(data) {

        const win =
            Number(
                data.win || 0,
            );


        const bet =
            Number(
                data.bet ||
                selectedBet ||
                0,
            );


        const balance =
            Number(
                data.balance || 0,
            );


        const multiplier =
            Number(
                data.multiplier || 0,
            );


        const fixedWin =
            data.fixed_win;


        /*
         * Update balance.
         */

        balanceBox.textContent =
            `${formatNumber(balance)} AP`;


        let resultText = "";

        let resultClass =
            "fortune-result";


        /* ================================================
           FIXED REWARDS
           ================================================ */

        if (
            fixedWin !== null &&
            fixedWin !== undefined
        ) {

            const fixed =
                Number(fixedWin);


            if (fixed >= 500_000) {

                resultText =
                    `👑🔥 ULTRA JACKPOT! +` +
                    `${formatNumber(fixed)} AP 🔥👑`;

                resultClass +=
                    " jackpot ultra-jackpot";


            } else if (fixed >= 200_000) {

                resultText =
                    `👑🔥 JACKPOT! +` +
                    `${formatNumber(fixed)} AP 🔥`;

                resultClass +=
                    " jackpot";


            } else if (fixed >= 10_000) {

                resultText =
                    `💰 +${formatNumber(fixed)} AP!`;

                resultClass +=
                    " big-win";


            } else {

                resultText =
                    `💰 +${formatNumber(fixed)} AP!`;

                resultClass +=
                    " win";
            }


        /* ================================================
           MULTIPLIERS
           ================================================ */

        } else if (multiplier >= 10) {

            resultText =
                `👑🔥 10x MEGA JACKPOT! ` +
                `+${formatNumber(win)} AP 🔥👑`;

            resultClass +=
                " jackpot";


        } else if (multiplier >= 7.5) {

            resultText =
                `🔥 7.5x! +` +
                `${formatNumber(win)} AP 🔥`;

            resultClass +=
                " big-win";


        } else if (multiplier >= 5) {

            resultText =
                `🔥 5x! +` +
                `${formatNumber(win)} AP 🔥`;

            resultClass +=
                " big-win";


        } else if (multiplier >= 3) {

            resultText =
                `🎉 ${multiplier}x! +` +
                `${formatNumber(win)} AP`;

            resultClass +=
                " big-win";


        } else if (multiplier >= 2) {

            resultText =
                `🎉 ${multiplier}x! +` +
                `${formatNumber(win)} AP`;

            resultClass +=
                " win";


        } else if (multiplier >= 1.5) {

            resultText =
                `✨ ${multiplier}x! +` +
                `${formatNumber(win)} AP`;

            resultClass +=
                " win";


        } else if (multiplier >= 1) {

            resultText =
                `1x · ${formatNumber(win)} AP`;

            resultClass +=
                " neutral";


        } else if (multiplier > 0) {

            resultText =
                `${multiplier}x · ` +
                `${formatNumber(win)} AP`;

            resultClass +=
                " loss-small";


        } else {

            resultText =
                "💀 0x · You lost the bet";

            resultClass +=
                " loss";
        }


        /* ================================================
           NET RESULT
           ================================================ */

        const netResult =
            win - bet;


        if (netResult > 0) {

            resultText +=
                ` · Net +${formatNumber(netResult)} AP`;

        } else if (netResult < 0) {

            resultText +=
                ` · Net ${formatNumber(netResult)} AP`;
        }


        resultBox.textContent =
            resultText;

        resultBox.className =
            resultClass;


        updateWheelLevel();
    }


    /* =====================================================
       SPIN BUTTON
       ===================================================== */

    spinButton.addEventListener(
        "click",
        spinWheel,
    );


    /* =====================================================
       INITIAL STATE
       ===================================================== */

    updateWheelLevel();

});
