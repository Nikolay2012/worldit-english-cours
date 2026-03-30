const calendar = document.getElementById("calendar")
const monthObject = document.getElementById("currentMonth")
const prevMonth = document.getElementById("prevMonth")
const nextMonth = document.getElementById("nextMonth")

let currentMonth = new Date().getMonth()
let currentYear = new Date().getFullYear()

const monthNames = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень','Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']

function getCalendarGrid(year, month) {
  const startDate = new Date(year, month, 1)
  const firstDayIndex = (startDate.getDay() + 6) % 7
  startDate.setDate(startDate.getDate() - firstDayIndex)

  const grid = []
  
  for (let weekIndex = 0; weekIndex < 6; weekIndex++) {
    const week = []
    for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
      week.push({
        number: startDate.getDate(),
        indexInWeek: dayIndex,
        isCurrentMonth: startDate.getMonth() === month
      })
      
      startDate.setDate(startDate.getDate() + 1)
    }
    grid.push(week)
  }
  
  return grid
}

function updateCalendar(){
    monthObject.textContent = `${monthNames[currentMonth]} ${currentYear}`
    calendar.innerHTML = ''
    const calendarGrid = getCalendarGrid(currentYear, currentMonth)
    calendarGrid.forEach(week=>{
        const weekObject = document.createElement('div')
        weekObject.classList.add("week")
        week.forEach(day=>{
            const dayObject = document.createElement('div')
            dayObject.classList.add("day-container")
            dayObject.innerHTML = `
                <span class = "day"><p>${day.number}</p></span>
            `
            weekObject.append(dayObject)
            if (! day.isCurrentMonth){
                dayObject.querySelector("p").classList.add("dissable")
            }else{
                // ЦВЕТА, НАПОЛНЕНИЕ
                // if (day.indexInWeek == 0){
                //     let time = "17:00"
                //     dayObject.querySelector('span').classList.add("day-lesson")
                //     dayObject.querySelector('span').innerHTML += `<p>${time}</p>`
                // }
                // if (day.indexInWeek == 1){
                //     dayObject.querySelector('span').classList.add("day-cancelled")
                //     dayObject.querySelector('span').innerHTML += `<p>-</p>`
                // }
                // if (day.indexInWeek == 2){
                //     let time = "17:00"
                //     dayObject.querySelector('span').classList.add("day-change")
                //     dayObject.querySelector('span').innerHTML += `<p>${time}</p>`
                // }
                // if (day.number > 19 && day.number < 23){
                //     dayObject.classList.add("day-holiday")
                //     if (day.number == 20){dayObject.classList.add("first-holiday")}
                //     if (day.number == 22){dayObject.classList.add("last-holiday")}
                // }
                if (day.number > 19 && day.number < 27){
                    dayObject.classList.add("day-holiday")
                    if (day.number == 20){dayObject.classList.add("first-holiday")}
                    if (day.number == 26){dayObject.classList.add("last-holiday")}
                }
            }
        })
        calendar.append(weekObject)
    })
}
updateCalendar()

prevMonth.addEventListener("click", ()=>{
    currentMonth -= 1
    if (currentMonth < 0){
        currentMonth = 11
        currentYear -= 1
    }
    updateCalendar()
})
nextMonth.addEventListener("click", ()=>{
    currentMonth += 1
    if (currentMonth > 11){
        currentMonth = 0
        currentYear += 1
    }
    updateCalendar()
})