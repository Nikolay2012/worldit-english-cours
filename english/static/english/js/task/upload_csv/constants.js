// Заголовки и подсказки
const CREATE_WORD_TITLE = "Додати нове слово";
const EDIT_WORD_TITLE = "Редагувати слово";
const DEFAULT_TITLE = "Завантаження списку слів";
const LIST_TITLE = "Список слів";
const DELETE_LIST_TITLE = "Видалити список слів?";
const DEFAULT_FILE_HINT = "Підтримується: .csv";

// Макс. размер csv - мегабайт, как MAX_CSV_SIZE на сервере
const MAX_CSV_SIZE = 1 * 1024 * 1024;
// Для загрузки картинок к словам
const MAX_IMAGE_SIZE = 2 * 1024 * 1024;
const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"];
const PLACEHOLDER_IMAGE_URL = uploadCsvModal.dataset.placeholderUrl;

const wordsByStepId = new Map();
