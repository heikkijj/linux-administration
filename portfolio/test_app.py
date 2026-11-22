import unittest
from unittest.mock import patch

import app


class CounterTests(unittest.TestCase):
    @patch('app.pymysql.connect')
    def test_source_increments_and_reads_in_one_transaction(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.rowcount = 1
        cursor.fetchone.return_value = (42,)

        with patch.object(app, 'COUNTER_BACKEND', 'mariadb'), \
                patch.object(app, 'COUNTER_ROLE', 'source'):
            self.assertEqual(app.record_visit(), 42)

        self.assertEqual(cursor.execute.call_count, 2)
        self.assertTrue(cursor.execute.call_args_list[0].args[0].startswith('UPDATE'))
        connection.commit.assert_called_once()
        connection.close.assert_called_once()

    @patch('app.pymysql.connect')
    def test_replica_page_reads_without_incrementing(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (42,)

        with patch.object(app, 'COUNTER_BACKEND', 'mariadb'), \
                patch.object(app, 'COUNTER_ROLE', 'replica'):
            response = app.app.test_client().get('/week4/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="replica-counter">42', response.data)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        cursor.execute.assert_called_once_with('SELECT count FROM visitor_counter WHERE id = 1')
        connection.close.assert_called_once()

    @patch('app.pymysql.connect')
    def test_replica_other_pages_do_not_increment(self, connect):
        cursor = connect.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (42,)

        with patch.object(app, 'COUNTER_BACKEND', 'mariadb'), \
                patch.object(app, 'COUNTER_ROLE', 'replica'):
            response = app.app.test_client().get('/week2/')

        self.assertEqual(response.status_code, 200)
        cursor.execute.assert_called_once_with('SELECT count FROM visitor_counter WHERE id = 1')

    def test_week4_shows_text_setup_cards(self):
        with patch.object(app, 'COUNTER_ROLE', 'source'):
            response = app.app.test_client().get('/week4/')

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        cards = html.split('<div class="carousel-slides">', 1)[1].split(
            '<div class="carousel-controls"', 1
        )[0]
        self.assertEqual(cards.count('class="carousel-slide"'), 13)
        self.assertNotIn('<img', cards)
        self.assertIn('binlog_do_db = portfilio_db', cards)
        self.assertIn('coordinates recorded in that dump', cards)

    @patch('app.pymysql.connect')
    def test_missing_counter_row_fails_explicitly(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        with self.assertRaisesRegex(RuntimeError, 'counter row is missing'):
            app.mariadb_counter()

        connection.commit.assert_not_called()
        connection.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
