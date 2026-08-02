/* =====================================================
   STELLA MARIS ADMIN.JS
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       SIDEBAR TOGGLE
    ===================================================== */

    const sidebar = document.querySelector(".sidebar");
    const toggle = document.querySelector(".menu-toggle");

    if (toggle && sidebar) {

        toggle.addEventListener("click", () => {

            sidebar.classList.toggle("active");

        });

        document.addEventListener("click", (e) => {

            if (
                window.innerWidth <= 992 &&
                !sidebar.contains(e.target) &&
                !toggle.contains(e.target)
            ) {

                sidebar.classList.remove("active");

            }

        });

    }

    /* =====================================================
       FLASH MESSAGE CLOSE
    ===================================================== */

    document.querySelectorAll(".alert-close").forEach(button => {

        button.addEventListener("click", () => {

            button.closest(".alert").remove();

        });

    });

    /* =====================================================
       PASSPORT PREVIEW
    ===================================================== */

    const passportInput = document.getElementById("passportInput");
    const passportPreview = document.getElementById("passportPreview");

    if (passportInput && passportPreview) {

        passportInput.addEventListener("change", e => {

            const file = e.target.files[0];

            if (!file) return;

            const reader = new FileReader();

            reader.onload = event => {

                passportPreview.src = event.target.result;

            };

            reader.readAsDataURL(file);

        });

    }

    /* =====================================================
       LOADING OVERLAY
    ===================================================== */

    const form = document.querySelector("form");
    const loading = document.getElementById("loadingOverlay");

    if (form && loading) {

        form.addEventListener("submit", () => {

            loading.style.display = "flex";

        });

    }

    /* =====================================================
       LIVE CLOCK
    ===================================================== */

    function updateClock() {

        const time = document.getElementById("liveTime");
        const date = document.getElementById("liveDate");
        const day = document.getElementById("liveDay");

        if (!time || !date || !day) return;

        const now = new Date();

        const days = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday"
        ];

        const months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ];

        let hour = now.getHours();
        const minute = String(now.getMinutes()).padStart(2, "0");
        const second = String(now.getSeconds()).padStart(2, "0");

        const ampm = hour >= 12 ? "PM" : "AM";

        hour = hour % 12 || 12;

        time.textContent =
            `${String(hour).padStart(2,"0")}:${minute}:${second} ${ampm}`;

        date.textContent =
            `${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;

        day.textContent = days[now.getDay()];

    }

    updateClock();

    setInterval(updateClock, 1000);

    /* =====================================================
       GRADE CHART
    ===================================================== */

    const gradeCanvas = document.getElementById("gradeChart");

    if (
        gradeCanvas &&
        typeof gradeCounts !== "undefined"
    ) {

        new Chart(gradeCanvas, {

            type: "doughnut",

            data: {

                labels: [

                    "Grade A",
                    "Grade B",
                    "Grade C",
                    "Grade F"

                ],

                datasets: [{

                    data: [

                        gradeCounts.A || 0,
                        gradeCounts.B || 0,
                        gradeCounts.C || 0,
                        gradeCounts.F || 0

                    ],

                    backgroundColor: [

                        "#2563eb",
                        "#10b981",
                        "#f59e0b",
                        "#ef4444"

                    ]

                }]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {

                        position: "bottom"

                    }

                }

            }

        });

    }

});