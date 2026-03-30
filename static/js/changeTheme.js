const changeTheme = document.getElementById("changeTheme")
const body = document.querySelector("body")

if (localStorage.getItem("DarkTheme") == "true"){
    body.classList.add("dark-body")
    changeTheme.querySelector("img").src = changeTheme.querySelector("img").src.replace("moon", "sun")
}

if (changeTheme){
    changeTheme.addEventListener('click', ()=>{
        body.classList.toggle("dark-body")
        if (body.classList.contains("dark-body")){
            localStorage.setItem("DarkTheme", "true")
            changeTheme.querySelector("img").src = changeTheme.querySelector("img").src.replace("moon", "sun")
        }else{
            localStorage.setItem("DarkTheme", "false")
            changeTheme.querySelector("img").src = changeTheme.querySelector("img").src.replace("sun", "moon")
        }
    })
}