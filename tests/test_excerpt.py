import unittest

from app.document_parser import extract_text
from app.domain.excerpt import select_excerpt, terms


def book(pages: int, topic_page: int) -> str:
    text = []
    for n in range(1, pages + 1):
        topic = "Eliminación de Gauss y determinantes de una matriz."
        body = topic if n == topic_page else "Espacios vectoriales y bases."
        text.append(f"[Página {n}]\n{body} " + "relleno " * 120)
    return "\n\n".join(text)


class ExcerptTests(unittest.TestCase):
    def test_short_text_is_untouched(self) -> None:
        self.assertEqual(select_excerpt("[Página 1]\nhola", "gauss", 1000), "[Página 1]\nhola")

    def test_keeps_the_pages_about_the_topic(self) -> None:
        excerpt = select_excerpt(book(200, 137), "reducción de Gauss y el determinante", 3000)
        self.assertIn("[Página 137]", excerpt)
        self.assertLessEqual(len(excerpt), 3000)
        self.assertIn("partes más relacionadas", excerpt)

    def test_without_matches_it_keeps_the_beginning(self) -> None:
        excerpt = select_excerpt(book(50, 0), "termodinámica", 2500)
        self.assertIn("[Página 1]", excerpt)
        self.assertNotIn("[Página 40]", excerpt)

    def test_pages_stay_in_document_order(self) -> None:
        text = book(30, 25) + "\n\n[Página 31]\nOtra vez Gauss y determinante."
        excerpt = select_excerpt(text, "Gauss determinante", 2500)
        self.assertLess(excerpt.index("[Página 25]"), excerpt.index("[Página 31]"))

    def test_terms_ignore_accents_and_filler(self) -> None:
        self.assertEqual(terms("Taller para reforzar la Eliminación de GAUSS"), {"elimin", "gauss"})

    def test_long_txt_is_no_longer_rejected(self) -> None:
        raw = ("\n".join(f"línea {i} sobre matrices" for i in range(5000))).encode()
        self.assertLessEqual(len(extract_text("libro.txt", raw, 6000, "matrices")), 6000)


if __name__ == "__main__":
    unittest.main()
