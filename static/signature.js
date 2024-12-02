document.addEventListener("DOMContentLoaded", function () {
    // Initialisation du canvas
    const canvas = document.getElementById("signature-pad");
    const ctx = canvas.getContext("2d");
    let drawing = false;

    // Événements pour dessiner sur le canvas
    canvas.addEventListener("mousedown", (e) => {
        drawing = true;
        ctx.beginPath();
        ctx.moveTo(e.offsetX, e.offsetY);
    });

    canvas.addEventListener("mousemove", (e) => {
        if (drawing) {
            ctx.lineTo(e.offsetX, e.offsetY);
            ctx.stroke();
        }
    });

    canvas.addEventListener("mouseup", () => {
        drawing = false;
    });

    canvas.addEventListener("mouseout", () => {
        drawing = false;
    });

    // Effacer le canvas
    document.getElementById("clear-signature").addEventListener("click", function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    });

    // Sauvegarder la signature
    document.getElementById("save-signature").addEventListener("click", function () {
        const signatureData = canvas.toDataURL("image/png"); // Signature encodée en base64

        const modal = document.getElementById("signatureModal");
        const role = modal.dataset.role;
        const name = modal.dataset.name;
        const date = modal.dataset.date;

        // Envoyer la signature au serveur
        fetch("/save_signature", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role, name, date, signature: signatureData }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    // Met à jour le DOM pour refléter la signature
                    const cell = document.querySelector(
                        `tr[data-name="${name}"][data-date="${date}"] .${role}-status`
                    );

                    if (cell) {
                        cell.textContent = "Signed";
                    }

                    // Fermer le modal
                    const bootstrapModal = bootstrap.Modal.getInstance(modal);
                    bootstrapModal.hide();
                } else {
                    alert("Failed to save signature: " + data.error);
                }
            })
            .catch((err) => {
                console.error("Error saving signature:", err);
                alert("An error occurred while saving the signature.");
            });
    });
});

// Fonction pour ouvrir le modal avec les données de contexte
function showSignatureModal(role, name, date) {
    const modal = document.getElementById("signatureModal");
    modal.dataset.role = role;
    modal.dataset.name = name;
    modal.dataset.date = date;

    // Réinitialise le canvas
    const canvas = document.getElementById("signature-pad");
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Ouvre le modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}
