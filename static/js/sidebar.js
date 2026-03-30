const openMobileMenu = document.getElementById("menu")
const closeMobileMenu = document.getElementById("closeMenu")
const sideMenu = document.querySelector("aside")

openMobileMenu.addEventListener("click", ()=>{
    sideMenu.style.display = "flex"
})
closeMobileMenu.addEventListener("click", ()=>{
    sideMenu.style.display = "none"
})

window.addEventListener('resize', ()=>{
    if (window.innerWidth > 750){
        sideMenu.style.display = "flex"
    }else{
        sideMenu.style.display = "none"
    }
});

document.querySelectorAll(".open-menu-btn").forEach(btn => {
    btn.addEventListener("click", function(event){
        event.preventDefault()
        btn.classList.toggle("select-open-menu")
        btn.closest("a").nextElementSibling.classList.toggle("hide-list")
    })
})

document.getElementById("back").addEventListener("click", function(){
    window.history.back()
})