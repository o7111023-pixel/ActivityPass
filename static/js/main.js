document.addEventListener("DOMContentLoaded", () => {
    const copyButton = document.querySelector(".copy-card-btn");

    if (!copyButton) {
        return;
    }

    copyButton.addEventListener("click", () => {
        const cardNumber = copyButton.dataset.cardNumber;

        if (!cardNumber) {
            return;
        }

        copyCardNumber(cardNumber, copyButton);
    });
});


function copyCardNumber(number, button) {
    if (!button) {
        button = document.querySelector(".copy-card-btn");
    }

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(number)
            .then(() => {
                showCopied(button);
            })
            .catch(() => {
                fallbackCopy(number, button);
            });

        return;
    }

    fallbackCopy(number, button);
}


function fallbackCopy(number, button) {
    const textarea = document.createElement("textarea");

    textarea.value = number;

    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    textarea.style.opacity = "0";

    document.body.appendChild(textarea);

    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    try {
        const successful = document.execCommand("copy");

        if (successful) {
            showCopied(button);
        } else {
            showCopyError();
        }

    } catch (error) {
        console.error("Copy failed:", error);
        showCopyError();
    }

    document.body.removeChild(textarea);
}


function showCopied(button) {
    if (!button) {
        return;
    }

    const oldText = button.textContent;

    button.textContent = "Copied ✓";
    button.disabled = true;

    setTimeout(() => {
        button.textContent = oldText;
        button.disabled = false;
    }, 1500);
}


function showCopyError() {
    alert("Could not copy the card number.");
}
