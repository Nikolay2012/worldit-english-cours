function blockContext(event) { 
    event.preventDefault(); 
    event.stopPropagation(); 
}

function blockKeys(e) {
    const k = e.key.toUpperCase();

    if (k === 'F12' || k == "DEAD") { 
        blockContext(e)
    }else if ((e.ctrlKey || e.metaKey) && e.shiftKey && (k === 'I' || k === 'J' || k === 'C')) {
      blockContext(e)
    }else if ((e.ctrlKey || e.metaKey) && (k === 'U' || k === 'S')) {
      blockContext(e)
    }else if (e.ctrlKey && e.shiftKey && k === 'C') { 
        blockContext(e);
    }
}

document.addEventListener('keydown', blockKeys, true);
document.addEventListener('contextmenu', blockContext, true);