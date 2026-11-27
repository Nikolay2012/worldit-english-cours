
let wordFormState = {
    mode: null, 
    stepId: null, 
    category: null
};

let sentenceFormState = {
    mode: null, 
    stepId: null,
    gaps: [],
    previewAnswer: null,
    zeroGaps: [],
    // Разделитльные знаки указанные в предложении
    marks: []
};

let imageStates = [];

let isOpenedFromWordsPanel = false;

let isOpenedFromSentencesPanel = false;