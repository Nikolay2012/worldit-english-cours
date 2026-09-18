const loginForm = document.getElementById("loginForm")
const inputUsername = document.getElementById("inputUsername")
const inputPassword = document.getElementById("inputPassword")

loginForm.addEventListener("submit", async (event)=>{
    document.querySelector(".error")?.remove()
    event.preventDefault()

    const errorText = document.createElement("span")
    errorText.classList.add("error")
    errorText.textContent = "Заповніть обовʼязкове поле"

    if (!inputUsername.value.trim()){
        loginForm.insertBefore(errorText, inputUsername.nextElementSibling)
    }
    else if (!inputPassword.value.trim()){
        loginForm.insertBefore(errorText, inputPassword.nextElementSibling)
    }
    else{
        const response = await fetch('login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.getElementsByName("csrfmiddlewaretoken")[0].value,
            },
            body: JSON.stringify({"username": inputUsername.value, "password": inputPassword.value})
        })
        if (!response.ok) {
            errorText.textContent = "Невірний логін або пароль"
            loginForm.insertBefore(errorText, document.getElementById("or-continue"))
        }else{
            window.location.href = "/"
        }
    }
})