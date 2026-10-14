function closeModal(){
    modalCover.style.opacity = 0
    setTimeout(() => {
        document.body.classList.remove("not-scroll")
        modalCover.style.display = 'none'
        document.querySelectorAll(".modal").forEach(modal=>{
            modal.style.display = "none"
        })
    }, 500)
}

function openModal(modal) {
    modalCover.style.top = `${document.body.scrollTop}px`
    document.body.classList.add("not-scroll")

    modal.style.display = 'flex'
    modalCover.style.display = 'flex'
    setTimeout(() => {modalCover.style.opacity = 1}, 50)
}

document.getElementById("createUser")?.addEventListener("click", ()=>{openModal(modalUser)})
document.getElementById("createGroup")?.addEventListener("click", ()=>{openModal(modalGroup)})
document.getElementById("createCourse")?.addEventListener("click", ()=>{openModal(modalCourse)})

document.querySelectorAll(".closeModal").forEach(close=>{
    close.addEventListener("click", closeModal)
})

modalCover.addEventListener("mousedown", (event)=>{if (event.target == modalCover){closeModal()}})