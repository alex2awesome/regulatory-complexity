from pipeline.procbench.solar_panel.prepare_forum_evaluation import author_group, is_test


def test_author_group_ignores_thread_and_installation_suffix():
    assert author_group("thread1__Same_User__spring_2023") == "sameuser"
    assert author_group("thread2__same-user") == "sameuser"
    assert is_test("stable") == is_test("stable")
