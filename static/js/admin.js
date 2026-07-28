/* =====================================================
PHASE 5
FLASH MESSAGE CLOSE
===================================================== */

document.querySelectorAll(".alert-close").forEach(button => {

    button.addEventListener("click", function(){

        this.parentElement.style.display = "none";

    });

});
/* =====================================================
PHASE 9
CALENDAR
===================================================== */

const today = new Date();

const months = [

"January","February","March","April","May","June",

"July","August","September","October","November","December"

];

const day = document.getElementById("calendarDay");

const month = document.getElementById("calendarMonth");

if(day){

    day.innerHTML = today.getDate();

    month.innerHTML = months[today.getMonth()] + " " + today.getFullYear();

}
/* =====================================================
PHASE 9
GRADE CHART
===================================================== */

const chartCanvas = document.getElementById("gradeChart");

if (chartCanvas) {

    new Chart(chartCanvas, {

        type: "doughnut",

        data: {

            labels: ["Grade A", "Grade B", "Grade C", "Grade F"],

            datasets: [{

                data: [
                    gradeCounts.A,
                    gradeCounts.B,
                    gradeCounts.C,
                    gradeCounts.F
                ],

                backgroundColor: [
                    "#2563eb",
                    "#10b981",
                    "#f59e0b",
                    "#ef4444"
                ]

            }]

        }

    });

}
/* =====================================================
LIVE CLOCK
===================================================== */

function updateClock() {

    const timeElement = document.getElementById("liveTime");
    const dateElement = document.getElementById("liveDate");
    const dayElement = document.getElementById("liveDay");

    if (!timeElement || !dateElement || !dayElement) {
        return;
    }

    const now = new Date();

    const days = [
        "Sunday","Monday","Tuesday","Wednesday",
        "Thursday","Friday","Saturday"
    ];

    const months = [
        "January","February","March","April",
        "May","June","July","August",
        "September","October","November","December"
    ];

    let hours = now.getHours();
    let minutes = now.getMinutes();
    let seconds = now.getSeconds();

    const ampm = hours >= 12 ? "PM" : "AM";

    hours = hours % 12;
    hours = hours ? hours : 12;

    hours = String(hours).padStart(2,"0");
    minutes = String(minutes).padStart(2,"0");
    seconds = String(seconds).padStart(2,"0");

    timeElement.textContent =
        `${hours}:${minutes}:${seconds} ${ampm}`;

    dateElement.textContent =
        `${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;

    dayElement.textContent =
        days[now.getDay()];

}

updateClock();

setInterval(updateClock,1000);
document.querySelectorAll(".alert-close").forEach(button => {
    button.addEventListener("click", function () {
        this.parentElement.remove();
    });
});
/* =====================================================
PHASE 6
PASSPORT PREVIEW
===================================================== */

const passportInput = document.getElementById("passportInput");

if(passportInput){

    passportInput.addEventListener("change",function(e){

        const file = e.target.files[0];

        if(file){

            const reader = new FileReader();

            reader.onload = function(event){

                document.getElementById("passportPreview").src = event.target.result;

            }

            reader.readAsDataURL(file);

        }

    });

}
/* =====================================================
PHASE 8
FORM VALIDATION
===================================================== */

const editForm = document.querySelector("form");

if(editForm){

    editForm.addEventListener("submit",function(){

        document.getElementById("loadingOverlay").style.display="flex";

    });

}