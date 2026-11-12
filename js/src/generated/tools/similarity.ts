// GENERATED from the API specification. Do not edit.
// Language-neutral text overlap: letter n-grams work for spaced and unspaced scripts alike.
const NOT_LETTER_OR_DIGIT = /[^\p{L}\p{N}]+/gu
const SPACES = /\s+/g
const NAME_GRAM = 2
const TEXT_GRAM = 3

function grams(text: string, n: number): Set<string> {
  const chars = [...text]
  const out = new Set<string>()
  for (let i = 0; i + n <= chars.length; i += 1) out.add(chars.slice(i, i + n).join(''))
  return out
}

function shared(a: Set<string>, b: Set<string>): number {
  let n = 0
  for (const g of a) if (b.has(g)) n += 1
  return n
}

const nameGrams = (s: string): Set<string> => grams(s.toLowerCase().replace(NOT_LETTER_OR_DIGIT, ''), NAME_GRAM)
const textGrams = (s: string): Set<string> => grams(s.toLowerCase().replace(SPACES, ' ').trim(), TEXT_GRAM)

// Dice overlap of letter pairs, ignoring case and separators: check_slot vs checkSlots is about 0.94.
export function nameSimilarity(a: string, b: string): number {
  const x = nameGrams(a)
  const y = nameGrams(b)
  const total = x.size + y.size
  return total ? (2 * shared(x, y)) / total : 0
}

// Jaccard overlap of three-letter runs, ignoring case and spacing.
export function textSimilarity(a: string, b: string): number {
  const x = textGrams(a)
  const y = textGrams(b)
  const common = shared(x, y)
  const union = x.size + y.size - common
  return union ? common / union : 0
}

// A name as lowercase words: book_slot, bookSlot and book-slot all give [book, slot].
export function nameWords(name: string): string[] {
  return name.replace(/([\p{Ll}\p{N}])(\p{Lu})/gu, '$1 $2').toLowerCase().split(/[^\p{L}\p{N}]+/u).filter(Boolean)
}
