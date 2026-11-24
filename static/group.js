// ==================================================
// DAILY EXPENSE SPLITTER - GROUP PAGE
// ==================================================


// ==================================================
// GET GROUP ID
// ==================================================

const pathParts = window.location.pathname.split("/");
const groupId = pathParts[pathParts.length - 1];


// ==================================================
// GET LOGGED-IN USER
// ==================================================

const currentUser = JSON.parse(
    localStorage.getItem("user") || "null"
);


// ==================================================
// API RESPONSE HANDLER
// ==================================================

async function readResponse(response) {

    const text = await response.text();

    let data;

    try {
        data = JSON.parse(text);
    } catch {
        throw new Error("Invalid response from server.");
    }

    if (!response.ok) {
        throw new Error(
            data.message || "Something went wrong."
        );
    }

    return data;
}


// ==================================================
// DASHBOARD NAVIGATION
// ==================================================

function goDashboard() {
    window.location.href = "/dashboard";
}


// ==================================================
// GROUP DETAILS
// ==================================================

async function loadGroupDetails() {

    const title = document.getElementById("groupTitle");

    try {

        const response = await fetch(
            `/groups/${groupId}/details`
        );

        const data = await readResponse(response);

        title.textContent = data.name;

    } catch (error) {

        console.error("Group details error:", error);

        title.textContent = "Unable to load group";
    }
}


// ==================================================
// LOAD GROUP MEMBERS
// ==================================================

async function loadMembers() {

    const container = document.getElementById(
        "membersContainer"
    );

    container.innerHTML = "<p>Loading members...</p>";

    try {

        const response = await fetch(
            `/groups/${groupId}/members`
        );

        const data = await readResponse(response);

        container.innerHTML = "";

        if (!data.members || data.members.length === 0) {

            container.innerHTML = "<p>No members found.</p>";

            return;
        }

        data.members.forEach(member => {

            const card = document.createElement("div");

            card.className = "group-card";

            const name = document.createElement("h3");
            name.textContent = member.name;

            const email = document.createElement("p");
            email.textContent = member.email;

            card.appendChild(name);
            card.appendChild(email);

            // REMOVE MEMBER BUTTON

            if (
                currentUser &&
                Number(currentUser.id) !== Number(member.id)
            ) {

                const removeButton =
                    document.createElement("button");

                removeButton.textContent = "Remove Member";

                removeButton.onclick = () => {
                    removeMember(member.id);
                };

                card.appendChild(removeButton);
            }

            container.appendChild(card);

        });

        await loadPaidByMembers();

    } catch (error) {

        console.error("Members error:", error);

        container.innerHTML =
            `<p>${error.message}</p>`;
    }
}


// ==================================================
// LOAD USERS FOR ADD MEMBER
// ==================================================

async function loadUsers() {

    const select = document.getElementById("userSelect");

    if (!select) return;

    select.innerHTML =
        '<option value="">Select User</option>';

    try {

        const response = await fetch("/users");

        const data = await readResponse(response);

        const users = data.users || [];

        users.forEach(user => {

            const option = document.createElement("option");

            option.value = user.id;

            option.textContent =
                `${user.name} (${user.email})`;

            select.appendChild(option);

        });

    } catch (error) {

        console.error("Users loading error:", error);
    }
}


// ==================================================
// ADD MEMBER
// ==================================================

async function addMember() {

    const userId = document.getElementById(
        "userSelect"
    ).value;

    const message = document.getElementById(
        "memberMessage"
    );

    if (!userId) {

        message.textContent = "Please select a user.";

        return;
    }

    try {

        const response = await fetch(
            `/groups/${groupId}/members`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    user_id: Number(userId)
                })
            }
        );

        const data = await readResponse(response);

        message.textContent =
            data.message || "Member added successfully!";

        document.getElementById("userSelect").value = "";

        await loadMembers();
        await loadBalances();

    } catch (error) {

        console.error("Add member error:", error);

        message.textContent = error.message;
    }
}


// ==================================================
// REMOVE MEMBER
// ==================================================

async function removeMember(userId) {

    const confirmRemove = confirm(
        "Are you sure you want to remove this member?"
    );

    if (!confirmRemove) return;

    try {

        const response = await fetch(
            `/groups/${groupId}/members/${userId}`,
            {
                method: "DELETE"
            }
        );

        const data = await readResponse(response);

        alert(
            data.message || "Member removed successfully!"
        );

        await loadMembers();
        await loadBalances();

    } catch (error) {

        console.error("Remove member error:", error);

        alert(error.message);
    }
}


// ==================================================
// LOAD MEMBERS IN EXPENSE PAID BY DROPDOWN
// ==================================================

async function loadPaidByMembers() {

    const paidBy = document.getElementById("paidBy");

    if (!paidBy) return;

    paidBy.innerHTML =
        '<option value="">Select Member</option>';

    try {

        const response = await fetch(
            `/groups/${groupId}/members`
        );

        const data = await readResponse(response);

        data.members.forEach(member => {

            const option = document.createElement("option");

            option.value = member.id;

            option.textContent = member.name;

            paidBy.appendChild(option);

        });

    } catch (error) {

        console.error("Paid by members error:", error);
    }
}


// ==================================================
// ADD EXPENSE
// ==================================================

async function saveExpense(event) {

    event.preventDefault();

    const description = document.getElementById(
        "expenseDescription"
    ).value.trim();

    const amount = Number(
        document.getElementById("expenseAmount").value
    );

    const category = document.getElementById(
        "expenseCategory"
    ).value;

    const expenseDate = document.getElementById(
        "expenseDate"
    ).value;

    const paidBy = Number(
        document.getElementById("paidBy").value
    );

    const message = document.getElementById(
        "expenseMessage"
    );

    if (
        !description ||
        amount <= 0 ||
        !category ||
        !expenseDate ||
        !paidBy
    ) {

        message.textContent =
            "Please fill all expense details.";

        return;
    }

    try {

        // SAVE EXPENSE

        const response = await fetch(
            `/groups/${groupId}/expenses`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    description: description,
                    amount: amount,
                    category: category,
                    expense_date: expenseDate,
                    paid_by: paidBy

                })
            }
        );

        const data = await readResponse(response);

        // SPLIT EXPENSE EQUALLY

        const expenseId = data.expense_id;

        if (!expenseId) {

            throw new Error(
                "Expense was saved, but its ID was not returned. Please check before trying again."
            );
        }

        const splitResponse = await fetch(
            `/expenses/${expenseId}/split`,
            {
                method: "POST"
            }
        );

        await readResponse(splitResponse);

        message.textContent =
            "Expense added and split successfully!";

        document.getElementById("expenseForm").reset();

        closeExpenseModal();

        await loadExpenses();
        await loadBalances();

    } catch (error) {

        console.error("Expense error:", error);

        message.textContent = error.message;
    }
}


// ==================================================
// DISPLAY EXPENSES
// ==================================================

async function loadExpenses() {

    const container = document.getElementById(
        "expensesContainer"
    );

    container.innerHTML = "<p>Loading expenses...</p>";

    try {

        const response = await fetch(
            `/groups/${groupId}/expenses`
        );

        const data = await readResponse(response);

        container.innerHTML = "";

        if (
            !data.expenses ||
            data.expenses.length === 0
        ) {

            container.innerHTML =
                "<p>No expenses yet.</p>";

            return;
        }

        data.expenses.forEach(expense => {

            const card = document.createElement("div");

            card.className = "expense-card";

            const title = document.createElement("h3");

            title.textContent = expense.description;

            const amount = document.createElement("p");

            amount.textContent =
                `Amount: ₹${Number(expense.amount).toFixed(2)}`;

            const category = document.createElement("p");

            category.textContent =
                `Category: ${expense.category}`;

            const paidBy = document.createElement("p");

            paidBy.textContent =
                `Paid by: ${expense.paid_by_name}`;

            const date = document.createElement("p");

            date.textContent =
                `Date: ${expense.expense_date}`;

            card.appendChild(title);
card.appendChild(amount);
card.appendChild(category);
card.appendChild(paidBy);
card.appendChild(date);

// EDIT EXPENSE BUTTON
const editButton = document.createElement("button");

editButton.textContent = "✏️ Edit Expense";
editButton.onclick = function () {
    editExpense(expense);
};

card.appendChild(editButton);


// DELETE EXPENSE BUTTON


const deleteButton = document.createElement("button");

deleteButton.textContent = "🗑️ Delete Expense";

deleteButton.style.marginTop = "10px";
deleteButton.style.backgroundColor = "#E11D48";
deleteButton.style.color = "white";
deleteButton.style.border = "none";
deleteButton.style.padding = "10px 15px";
deleteButton.style.borderRadius = "6px";
deleteButton.style.cursor = "pointer";

deleteButton.onclick = function () {
    deleteExpense(expense.id);
};

card.appendChild(deleteButton);

container.appendChild(card);

        });

    } catch (error) {

        console.error("Expenses error:", error);

        container.innerHTML =
            `<p>${error.message}</p>`;
    }
}


// ==================================================
// DISPLAY GROUP BALANCES
// ==================================================

async function loadBalances() {

    const container = document.getElementById(
        "balancesContainer"
    );

    container.innerHTML = "<p>Loading balances...</p>";

    try {

        const response = await fetch(
            `/groups/${groupId}/balances`
        );

        const data = await readResponse(response);

        container.innerHTML = "";

        if (
            !data.balances ||
            data.balances.length === 0
        ) {

            container.innerHTML =
                "<p>No balances available.</p>";

            return;
        }

        data.balances.forEach(member => {

            const card = document.createElement("div");

            card.className = "balance-card";

            const name = document.createElement("h3");

            name.textContent = member.name;

            const paid = document.createElement("p");

            paid.textContent =
                `Total Paid: ₹${Number(member.total_paid).toFixed(2)}`;

            const owed = document.createElement("p");

            owed.textContent =
                `Total Owed: ₹${Number(member.total_owed).toFixed(2)}`;

            const balance = document.createElement("p");

            balance.textContent =
                `Balance: ₹${Number(member.balance).toFixed(2)}`;

            const status = document.createElement("strong");

            status.textContent = member.status;

            card.appendChild(name);
            card.appendChild(paid);
            card.appendChild(owed);
            card.appendChild(balance);
            card.appendChild(status);

            container.appendChild(card);

        });

    } catch (error) {

        console.error("Balances error:", error);

        container.innerHTML =
            `<p>${error.message}</p>`;
    }
}


// ==================================================
// SETTLEMENT SYSTEM
// ==================================================


// LOAD MEMBERS IN PAYMENT DROPDOWNS

async function loadPaymentMembers() {

    const paidBy = document.getElementById(
        "paymentPaidBy"
    );

    const paidTo = document.getElementById(
        "paidTo"
    );

    if (!paidBy || !paidTo) return;

    paidBy.innerHTML =
        '<option value="">Select Member</option>';

    paidTo.innerHTML =
        '<option value="">Select Member</option>';

    try {

        const response = await fetch(
            `/groups/${groupId}/members`
        );

        const data = await readResponse(response);

        data.members.forEach(member => {

            const option1 = document.createElement("option");

            option1.value = member.id;

            option1.textContent = member.name;

            const option2 = document.createElement("option");

            option2.value = member.id;

            option2.textContent = member.name;

            paidBy.appendChild(option1);

            paidTo.appendChild(option2);

        });

    } catch (error) {

        console.error("Payment members error:", error);
    }
}


// RECORD PAYMENT

async function savePayment(event) {

    event.preventDefault();

    const paidBy = Number(
        document.getElementById("paymentPaidBy").value
    );

    const paidTo = Number(
        document.getElementById("paidTo").value
    );

    const amount = Number(
        document.getElementById("paymentAmount").value
    );

    const paymentMethod =
        document.getElementById("paymentMethod").value;

    const transactionId =
        document.getElementById("transactionId").value.trim();

    const message = document.getElementById(
        "paymentMessage"
    );

    if (
        !paidBy ||
        !paidTo ||
        paidBy === paidTo ||
        amount <= 0
    ) {

        message.textContent =
            "Please select different members and enter a valid amount.";

        return;
    }

    try {

        const response = await fetch(
            `/groups/${groupId}/payments`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    paid_by: paidBy,
                    paid_to: paidTo,
                    amount: amount,
                    payment_method: paymentMethod,
                    transaction_id: transactionId

                })
            }
        );

        const data = await readResponse(response);

        message.textContent =
            data.message || "Payment recorded successfully!";

        document.getElementById("paymentForm").reset();

        await loadPaymentHistory();

    } catch (error) {

        console.error("Payment error:", error);

        message.textContent = error.message;
    }
}


// DISPLAY PAYMENT HISTORY

async function loadPaymentHistory() {

    const container = document.getElementById(
        "paymentHistory"
    );

    if (!container) return;

    try {

        const response = await fetch(
            `/groups/${groupId}/payments`
        );

        const data = await readResponse(response);

        container.innerHTML = "";

        if (
            !data.payments ||
            data.payments.length === 0
        ) {

            container.textContent =
                "No payments recorded yet.";

            return;
        }

        data.payments.forEach(payment => {

            const card = document.createElement("div");

            card.className = "payment-card";

            const title = document.createElement("h3");

            title.textContent =
                `${payment.paid_by_name} → ${payment.paid_to_name}`;

            const amount = document.createElement("p");

            amount.textContent =
                `Amount: ₹${Number(payment.amount).toFixed(2)}`;

            const method = document.createElement("p");

            method.textContent =
                `Method: ${payment.payment_method}`;

            const status = document.createElement("p");

            status.textContent =
                `Status: ${payment.status}`;

            card.appendChild(title);
            card.appendChild(amount);
            card.appendChild(method);
            card.appendChild(status);

            container.appendChild(card);

        });

    } catch (error) {

        console.error("Payment history error:", error);

        container.textContent =
            "Unable to load payment history.";
    }
}


// ==================================================
// MEMBER MODAL
// ==================================================

function openMemberModal() {

    document.getElementById(
        "memberModal"
    ).style.display = "block";

    document.getElementById(
        "memberMessage"
    ).textContent = "";

    loadUsers();
}


function closeMemberModal() {

    document.getElementById(
        "memberModal"
    ).style.display = "none";
}


// ==================================================
// EXPENSE MODAL
// ==================================================

function openExpenseModal() {

    document.getElementById(
        "expenseModal"
    ).style.display = "block";

    document.getElementById(
        "expenseMessage"
    ).textContent = "";

    loadPaidByMembers();
}


function closeExpenseModal() {

    document.getElementById(
        "expenseModal"
    ).style.display = "none";
}

// ==================================================
// PAGE INITIALIZATION
// ==================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("Group JavaScript loaded successfully.");

    if (!groupId || isNaN(Number(groupId))) {

        console.error("Invalid group ID.");

        return;
    }

    // GROUP INFORMATION

    loadGroupDetails();

    // MEMBERS

    loadMembers();

    // EXPENSES

    loadExpenses();

    // BALANCES

    loadBalances();

    // PAYMENT INFORMATION

    loadPaymentMembers();

    loadPaymentHistory();

    // EXPENSE FORM

    const expenseForm = document.getElementById(
        "expenseForm"
    );

    if (expenseForm) {

        expenseForm.addEventListener(
            "submit",
            saveExpense
        );
    }

    // PAYMENT FORM

    const paymentForm = document.getElementById(
        "paymentForm"
    );

    if (paymentForm) {

        paymentForm.addEventListener(
            "submit",
            savePayment
        );
    }

    // UPI FORM

const upiForm = document.getElementById("upiForm");

if (upiForm) {

    upiForm.addEventListener(
        "submit",
        saveMyUpiId
    );

    loadMyUpiId();
}
    // SET TODAY'S DATE

    const dateInput = document.getElementById(
        "expenseDate"
    );

    if (dateInput) {

        dateInput.value =
            new Date().toISOString().split("T")[0];
    }

});

// OPEN SETTLEMENT PAGE

function openSettlement() {
    window.location.href = `/settlement/${groupId}`;
}
// ==========================================
// DELETE INDIVIDUAL EXPENSE
// ==========================================

async function deleteExpense(expenseId) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this expense?"
    );

    if (!confirmDelete) {
        return;
    }

    try {

        const response = await fetch(
            `/expenses/${expenseId}`,
            {
                method: "DELETE"
            }
        );

        const data = await readResponse(response);

        alert(data.message);

        // Refresh expenses
        await loadExpenses();

        // Refresh balances
        await loadBalances();

    } catch (error) {

        console.error("Delete expense error:", error);

        alert(error.message);
    }
}
// ==========================================
// DELETE INDIVIDUAL EXPENSE
// ==========================================

async function deleteExpense(expenseId) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this expense?"
    );

    if (!confirmDelete) return;

    try {

        const response = await fetch(
            `/expenses/${expenseId}`,
            {
                method: "DELETE"
            }
        );

        const data = await readResponse(response);

        alert(data.message);

        // Refresh expenses and balances
        await loadExpenses();
        await loadBalances();

    } catch (error) {

        console.error("Delete expense error:", error);

        alert(error.message);
    }
}
// ==========================================
// EDIT INDIVIDUAL EXPENSE
// ==========================================

async function editExpense(expense) {

    const description = prompt(
        "Enter expense description:",
        expense.description
    );

    if (description === null) return;

    const amount = prompt(
        "Enter expense amount:",
        expense.amount
    );

    if (amount === null) return;

    const category = prompt(
        "Enter expense category:",
        expense.category
    );

    if (category === null) return;

    const expense_date = prompt(
        "Enter expense date (YYYY-MM-DD):",
        expense.expense_date
    );

    if (expense_date === null) return;

    const paid_by = prompt(
        "Enter payer user ID:",
        expense.paid_by
    );

    if (paid_by === null) return;

    try {

        const response = await fetch(
            `/expenses/${expense.id}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    description: description,
                    amount: amount,
                    category: category,
                    expense_date: expense_date,
                    paid_by: paid_by
                })
            }
        );

        const data = await readResponse(response);

        alert(data.message);

        await loadExpenses();
        await loadBalances();

    } catch (error) {

        console.error("Edit expense error:", error);
        alert(error.message);
    }
}
