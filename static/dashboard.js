// =========================
// GET LOGGED IN USER
// =========================

let user = null;

try {
    user = JSON.parse(localStorage.getItem("user"));
} catch (error) {
    console.error("Invalid user data:", error);
}


// =========================
// CHECK LOGIN
// =========================

if (!user || !user.id) {

    localStorage.removeItem("user");

    window.location.href = "/";

}


// =========================
// SHOW USER NAME
// =========================

document.getElementById("welcomeText").innerText =
    "Welcome, " + user.name + " 👋";


document.getElementById("sidebarUserName").innerText =
    user.name;


// =========================
// LOGOUT
// =========================

function logout() {

    localStorage.removeItem("user");

    window.location.href = "/";

}


// =========================
// OPEN CREATE GROUP
// =========================

function openCreateGroup() {

    document.getElementById("groupModal").style.display = "block";

    document.getElementById("groupMessage").innerText = "";

}


// =========================
// CLOSE CREATE GROUP
// =========================

function closeCreateGroup() {

    document.getElementById("groupModal").style.display = "none";

}


// =========================
// CREATE GROUP
// =========================

async function createGroup() {

    const name = document
        .getElementById("groupName")
        .value.trim();

    const message = document.getElementById("groupMessage");

    const button = document.querySelector(
        "#groupModal .modal-content button"
    );

    if (!name) {

        message.innerText = "Please enter a group name.";

        return;
    }

    try {

        button.disabled = true;

        button.innerText = "Creating...";

        const response = await fetch("/groups", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                name: name,

                created_by: user.id

            })

        });

        const data = await response.json();

        if (!response.ok) {

            message.innerText =
                data.message || "Unable to create group.";

            return;
        }

        message.innerText =
            data.message || "Group created successfully!";

        document.getElementById("groupName").value = "";

        // REFRESH DASHBOARD

        await loadDashboard();

        setTimeout(() => {

            closeCreateGroup();

        }, 700);

    } catch (error) {

        console.error("Create group error:", error);

        message.innerText = "Server error. Please try again.";

    } finally {

        button.disabled = false;

        button.innerText = "Create Group";

    }

}


// =========================
// LOAD GROUPS
// =========================

async function loadGroups() {

    const container =
        document.getElementById("groupsContainer");

    try {

        const response = await fetch(`/groups/${user.id}`);

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.message || "Unable to load groups."
            );

        }

        container.innerHTML = "";

        const groups = data.groups || [];

        document.getElementById("groupCount").innerText =
            groups.length;

        if (groups.length === 0) {

            container.innerHTML =
                "<p>No groups created yet.</p>";

            return groups;

        }

        groups.forEach(function(group) {

            const card = document.createElement("div");

            card.className = "group-card";


            // GROUP NAME

            const heading = document.createElement("h3");

            heading.textContent = "👥 " + group.name;


            // GROUP ID

            const groupId = document.createElement("p");

            groupId.textContent = "Group ID: " + group.id;


            // OPEN GROUP BUTTON

            const button = document.createElement("button");

            button.textContent = "Open Group";

            button.addEventListener("click", function() {

                openGroup(group.id);

            });


            card.appendChild(heading);

            card.appendChild(groupId);

            card.appendChild(button);

            container.appendChild(card);

        });

        return groups;

    } catch (error) {

        console.error("Error loading groups:", error);

        container.innerHTML =
            "<p>Unable to load groups. Please refresh the page.</p>";

        document.getElementById("groupCount").innerText = "0";

        return [];

    }

}


// =========================
// LOAD FINANCIAL SUMMARY
// =========================

async function loadSummary(groups) {

    let totalYouGet = 0;

    let totalYouOwe = 0;

    try {

        for (const group of groups) {

            const response = await fetch(
                `/groups/${group.id}/balances`
            );

            const data = await response.json();

            if (!response.ok) {

                console.error(
                    "Balance error:",
                    group.id,
                    data.message
                );

                continue;

            }

            const balances = data.balances || [];


            // FIND CURRENT USER BALANCE

            const myBalance = balances.find(member =>

                Number(member.user_id) === Number(user.id)

            );

            if (!myBalance) {

                continue;

            }

            const balance = Number(myBalance.balance) || 0;


            // POSITIVE = YOU GET

            if (balance > 0.01) {

                totalYouGet += balance;

            }


            // NEGATIVE = YOU OWE

            else if (balance < -0.01) {

                totalYouOwe += Math.abs(balance);

            }

        }


        // DISPLAY BALANCES

        document.getElementById("youGet").innerText =
            "₹" + totalYouGet.toFixed(2);

        document.getElementById("youOwe").innerText =
            "₹" + totalYouOwe.toFixed(2);

    } catch (error) {

        console.error("Summary calculation error:", error);

    }

}


// =========================
// OPEN GROUP
// =========================

function openGroup(groupId) {

    window.location.href = `/group/${groupId}`;

}


// =========================
// LOAD COMPLETE DASHBOARD
// =========================

async function loadDashboard() {

    const groups = await loadGroups();

    await loadSummary(groups);

}


// =========================
// START DASHBOARD
// =========================

loadDashboard();