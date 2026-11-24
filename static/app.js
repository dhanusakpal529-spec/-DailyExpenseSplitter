// =========================
// SHOW LOGIN
// =========================

function showLogin() {

    document.getElementById("loginBox").style.display = "block";

    document.getElementById("registerBox").style.display = "none";
}


// =========================
// SHOW REGISTER
// =========================

function showRegister() {

    document.getElementById("loginBox").style.display = "none";

    document.getElementById("registerBox").style.display = "block";
}


// =========================
// REGISTER
// =========================

async function register() {

    const name = document.getElementById("registerName").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;

    // Check empty fields
    if (!name || !email || !password) {

        document.getElementById("registerMessage").innerText =
            "Please fill all fields";

        return;
    }

    try {

        const response = await fetch("/register", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name: name,
                email: email,
                password: password
            })

        });

        const data = await response.json();

        document.getElementById("registerMessage").innerText =
            data.message;

        // If registration is successful
        if (response.ok) {

            // Clear fields
            document.getElementById("registerName").value = "";
            document.getElementById("registerEmail").value = "";
            document.getElementById("registerPassword").value = "";

            // Show login form
            showLogin();
        }

    } catch (error) {

        document.getElementById("registerMessage").innerText =
            "Server error. Please try again.";

        console.error(error);
    }
}


// =========================
// LOGIN
// =========================

async function login() {

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    // Check empty fields
    if (!email || !password) {

        document.getElementById("loginMessage").innerText =
            "Please enter email and password";

        return;
    }

    try {

        const response = await fetch("/login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })

        });

        const data = await response.json();

        document.getElementById("loginMessage").innerText =
            data.message;


        // LOGIN SUCCESS
        if (response.ok) {

            console.log("Logged in user:", data.user);

            // Save user information
            localStorage.setItem(
                "user",
                JSON.stringify(data.user)
            );

            // Go to Dashboard
            window.location.href = "/dashboard";
        }

    } catch (error) {

        document.getElementById("loginMessage").innerText =
            "Server error. Please start Flask server.";

        console.error(error);
    }
}