import mysql.connector

__author__ = 'ddMax'


class BaseSpider(object):

    def savetodb(self, table_name, dicdata):
        conn = mysql.connector.connect(host='115.159.2.146', user='root', password='{ddmax}', database='zjnucloud')
        cursor = conn.cursor()

        # Convert dict into column->value
        column = ''
        row = r''
        for key in dicdata.keys():
            try:
                column = column + ' ' + key + ','
                # The field type is Integer
                if key == 'articleId' or key == 'id':
                    # row = (row + '%d' + ',') % (dicdata[key]) #坑！
                    row += r'{},'.format(dicdata[key])
                # The field type is varchar
                else:
                    # row = (row + '"%s"' + ',') % (dicdata[key]) #坑！
                    row += r'"{}",'.format(dicdata[key])
            except ValueError as e:
                print('错误：{}'.format(e))

        # Insert a row of news
        try:
            sql = 'REPLACE INTO %s(%s) VALUES (%s)' % (table_name, column[:-1], row[:-1])
            cursor.execute(sql)
        except mysql.connector.Error as e:
            print('Error: {}'.format(e))
        conn.commit()
        cursor.close()
        conn.close()

    # Escape sequences \" and \'
    def patchstr(self, s):
        patched = s
        if patched.find('"') != -1:
            patched = patched.replace(r'"', r'\"')
        if patched.find("'") != -1:
            patched = patched.replace(r"'", r"\'")
        return patched
