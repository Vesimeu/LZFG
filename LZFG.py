import math

def ceil_log2(x):
    return math.ceil(math.log2(x)) if x > 0 else 1

def find_best_match(text, pos, max_len=17):
    best_length = 0
    best_index = None
    # Поиск по уже обработанной части (окно имеет длину pos, если pos < W)
    for i in range(0, pos):
        length = 0
        # Сравниваем символы, но не более max_len символов
        while length < max_len and pos + length < len(text) and text[i+length] == text[pos+length]:
            length += 1
        if length > best_length:
            best_length = length
            best_index = i
    return best_length, best_index

def can_find_pointer_at(text, pos, window_end, max_len=17):
    """Проверяет, можно ли, начиная с позиции pos, найти совпадение длиной >= 3 в окне [0, window_end)"""
    if pos >= len(text):
        return False
    best_length, _ = find_best_match(text, pos, max_len)
    return best_length >= 3

def choose_literal_length(text, pos, max_literal=16, max_len=17):
    # Начинаем с 1 символа и расширяем блок, если в дальнейшем нет возможности получить ссылку
    L = 1
    while L < max_literal and pos + L < len(text):
        # Если уже в следующем символе появляется возможность ссылочного кодирования, прекращаем накопление
        if can_find_pointer_at(text, pos + L, pos + L):
            break
        L += 1
    return L

def compress_LZFG(text):
    pos = 0
    step = 1
    steps = []
    total_cost = 0
    while pos < len(text):
        # Если в окне недостаточно символов для поиска ссылки – передаём литералы
        if pos < 3:
            L = min(16, len(text) - pos)
            literal_block = text[pos:pos+L]
            # Кодовая комбинация: 4 бита нулей + 4-битное представление (L-1)
            code = "0000 " + format(L - 1, '04b') + " bin(" + literal_block + ")"
            cost = 8 + 8 * L  # 8 бит служебного кода + 8 бит на каждый символ
            steps.append({
                "step": step,
                "match_length": 0,
                "distance": None,
                "literal_count": L,
                "code": code,
                "transmitted": literal_block,
                "cost": cost,
                "window": pos  # фактическая длина окна
            })
            pos += L
            total_cost += cost
            step += 1
            continue

        # Пытаемся найти самое длинное совпадение в окне [0, pos)
        best_length, best_index = find_best_match(text, pos, max_len=17)
        if best_length >= 3:
            # Для ссылочного кода:
            # – поле длины – 4 бита, кодируем значение (match_length - 2)
            length_code = format(best_length - 2, '04b')
            # Вычисляем расстояние: стандартно distance = pos - best_index,
            # но кодируется значение (distance - 1)
            actual_distance = pos - best_index
            stored_distance = actual_distance - 1
            # Количество бит для расстояния определяется как ceil(log2(эффективного окна))
            dist_bits = ceil_log2(pos)
            distance_code = format(stored_distance, '0{}b'.format(dist_bits))
            code = length_code + " " + distance_code
            cost = 4 + dist_bits  # 4 бита на длину + dist_bits
            token = text[pos:pos+best_length]
            steps.append({
                "step": step,
                "match_length": best_length,
                "distance": (stored_distance, pos),  # (хранимое значение, фактическое окно = pos)
                "literal_count": None,
                "code": code,
                "transmitted": token,
                "cost": cost,
                "window": pos
            })
            pos += best_length
            total_cost += cost
            step += 1
        else:
            # Если ссылки найти не удалось – передаём блок литералов
            L = choose_literal_length(text, pos, max_literal=16)
            literal_block = text[pos:pos+L]
            code = "0000 " + format(L - 1, '04b') + " bin(" + literal_block + ")"
            cost = 8 + 8 * L
            steps.append({
                "step": step,
                "match_length": 0,
                "distance": None,
                "literal_count": L,
                "code": code,
                "transmitted": literal_block,
                "cost": cost,
                "window": pos
            })
            pos += L
            total_cost += cost
            step += 1
    return steps, total_cost

def print_table(steps, total_cost):
    # Вывод заголовка таблицы
    header = f"{'Шаг':<4} {'Длина совп.':<14} {'Расст. до обр.':<18} {'Число букв':<14} {'Кодовые символы':<25} {'Перед. буквы':<20} {'Затраты (бит)':<15}"
    print(header)
    print("-" * len(header))
    for s in steps:
        step = s["step"]
        match_len = s["match_length"]
        if match_len >= 3:
            # Для ссылки: выводим расстояние в виде "stored(окно)"
            stored, win = s["distance"]
            dist_field = f"{stored}({win})"
            literal_count = "-"
        else:
            dist_field = "-"
            literal_count = s["literal_count"]
        print(f"{step:<4} {str(match_len):<14} {dist_field:<18} {str(literal_count):<14} {s['code']:<25} {s['transmitted']:<20} {s['cost']:<15}")
    print("-" * len(header))
    print(f"{'Итого':<81} {total_cost}")

if __name__ == "__main__":
    # Тестовое кодовое слово
    text = "IF_WE_CANNOT_DO_AS_WE_WOULD_WE_SHOULD_DO_AS_WE_CAN"
    steps, total_cost = compress_LZFG(text)
    print_table(steps, total_cost)
