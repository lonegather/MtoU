# -*- coding: utf-8 -*-


def reset():
    import os
    import csv
    from main import models

    tables = [
        models.Role,
        models.Project, models.Genus, models.Tag,
        models.Entity, models.Stage, models.Task
    ]

    for table in tables:
        for row in table.objects.all():
            row.delete()

    data = {}
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'setup.csv')
    with open(csv_path, encoding='gb2312') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        rows = [row for row in csv_reader]
        cols = [col for col in zip(*rows)]
        for header in rows[0]:
            table, field = header.split('|')
            for col in cols:
                if col[0] == header:
                    if not data.get(table, None):
                        data[table] = list()
                        for value in col[1:]:
                            if value:
                                data[table].append({field: value})
                    else:
                        for i in range(len(col[1:])):
                            if col[1:][i]:
                                data[table][i][field] = col[1:][i]
                    break

    instantiate(data)


def instantiate(data, table=None):
    from . import models
    if not table:
        for table in data:
            instantiate(data, table)
        return

    for i in range(len(data[table])):
        row = data[table][i]
        if type(row) is dict:
            for ref in foreign_key(data, table):
                if ref == 'User':
                    continue
                instantiate(data, ref)
            row_edit = {}
            for k, v in row.items():
                if '|' in v:
                    target, name = v.split('|')
                    if not name:
                        continue
                    target_class = getattr(models, target)
                    kwarg = 'username' if target == 'User' else 'name'
                    row[k] = target_class.objects.get(**{kwarg: name})
                row_edit[k] = row[k]
            table_class = getattr(models, table)
            data[table][i] = table_class(**row_edit)
            data[table][i].save()


def foreign_key(data, table):
    for row in data[table]:
        if type(row) is dict:
            for k, v in row.items():
                if '|' in v:
                    yield v.split('|')[0]


if __name__ == "__main__":
    reset()
