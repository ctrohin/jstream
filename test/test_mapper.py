from baseTest import BaseTestCase
from jstreams.mapper import Mapper, MapperWith, mapper_of, mapper_with_of


class TestMapper(BaseTestCase):
    def test_mapper(self):
        def fn(x):
            return x + 1

        self.assertEqual(mapper_of(fn), Mapper.of(fn))
        self.assertEqual(mapper_of(Mapper.of(fn)), Mapper.of(fn))
        self.assertNotEqual(mapper_of(fn), lambda x: x + 1)

    def test_mapper_with(self):
        def fn(x, y):
            return x + y

        self.assertEqual(mapper_with_of(fn), MapperWith.of(fn))
        self.assertEqual(mapper_with_of(MapperWith.of(fn)), MapperWith.of(fn))
        self.assertNotEqual(mapper_with_of(fn), lambda x, y: x + y)
