const grassBack = document.querySelector("#grassBack")
const grassFront = document.querySelector("#grassFront")
const character = document.querySelector("#character")
const bird = document.querySelector("#bird")
const mainBg = document.querySelector("#mainBg")

function startPage1Animation() {
    grassInterval = setInterval(() => {
        grassBack.src = grassBack.src.split('-')[0] + (grassBack.src.split('-')[1] == "1.webp" ? "-2.webp" : "-1.webp")
        grassFront.src = grassFront.src.split('-')[0] + (grassFront.src.split('-')[1] == "1.webp" ? "-2.webp" : "-1.webp")
    }, 400);
    characterInterval = setInterval(()=>{
        character.src = character.src.split("character")[0] + "character.webp"
        setTimeout(() => {
            character.src = character.src.split("character")[0] + "characterSit.webp"
        }, 1950);
    }, 10000)

    if (bird && windowWidth > 700){
        birdMoveInterval = moveImg(bird, -6, 100, 15000, 5000)
    }
}

function stopPage1Animation() {
    clearInterval(grassInterval)
    clearInterval(characterInterval)
    clearInterval(birdMoveInterval)
}

document.addEventListener("DOMContentLoaded", ()=>{
    setTimeout(() => {
        character.src = character.src.split("character")[0] + "character.webp"
        setTimeout(() => {
            character.src = character.src.split("character")[0] + "characterSit.webp"
        }, 1950);
    }, 2000);
})