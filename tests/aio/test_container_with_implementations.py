from di.aio import AioContainer


class MyDep:
    def __init__(self, *, nums: list[int]):
        self._sum = sum(nums)

    def total(self) -> int:
        return self._sum


async def test_implementations():
    my_container = AioContainer()
    my_container += 1
    my_container += 2
    my_container += 3
    my_container += 4
    my_container += MyDep
    my_dep = await my_container.get_component(MyDep)
    assert my_dep.total() == 10
