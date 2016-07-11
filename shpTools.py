# coding= UTF-8
# author:shikanon
import arcpy
import numpy as np
import pandas as pd

def Shp2dataframe(path):
    '''将arcpy表单变为pandas表单输出'''
    fields=arcpy.ListFields(path)
    table=[]
    fieldname=[field.name for field in fields]
    #游标集合，用for 循环一次后没办法循环第二次!一个游标实例只能循环一次
    data=arcpy.SearchCursor(path)
    for row in data:
        #Shape字段中的要数是一个几何类
        r=[]
        for field in fields:
            r.append(row.getValue(field.name))
        table.append(r)
    return pd.DataFrame(table,columns=fieldname)

#将由ReadTable读取的pandas表转换为shp格式,template为模板,如果template为'',则geoType必须不为空
def Dataframe2ShpTemplate(df,outpath,geoType,template):
    '''
    Fuction:
    make the table of pandas's DataFrame convert to the shp of esri
    Input:
    df -- pandas DataFrame from the shp converted
    outpath -- the shp output path
    geometryType -- the type of geomentey, eg:'POINT','POLYLINE','POLYGON','MULTIPOINT'
    temple -- the temple, at most time it is used the DataFrame's shp
    '''
    out_path = outpath.replace(outpath.split('/')[-1],'')
    out_name = outpath.split('/')[-1]
    geometry_type = geoType
    #template为模板，可以将里面属性全部赋予新建的要素，包括字段、坐标系
    feature_class = arcpy.CreateFeatureclass_management(
        out_path, out_name, geometry_type, template)
    #新生成的shp图形信息
    desc = arcpy.Describe(outpath)
    if template=='':
        fields = set(list(df.columns)+['Shape','FID'])
        originfieldnames = [field.name for field in desc.fields]
        for fieldname in fields:
            #判断字段是否存在然后加入新字段
            if fieldname not in originfieldnames:
                arcpy.AddField_management(outpath,fieldname,'TEXT')
    #'*'表示插入所有字段
    #cursor = arcpy.da.InsertCursor(outpath,'*')
    for row in df.index:
        #Shape需要改为'SHAPE@'才可以写入
        df['SHAPE@'] = df['Shape']
        cursor = arcpy.da.InsertCursor(outpath,[field for field in df.columns])
        cursor.insertRow([df[field][row] for field in df.columns])
    print 'Pandas to shp finish!'
    del cursor

#输入为经纬度列表,输入为polyline类型,可以用list[]组成feature,
#用CopyFeatures_management生成shp文件
def drawLine(lineCoord):
    '''
    Input:
    linecoord-- lineCoord = ['lng,lat','lng,lat',...]
    Output: a type of polyline'''
    # Create a Polyline object based on the array of points
    # Append to the list of Polyline objects
    lineCoord = [[float(c[0]),float(c[1])] for c in lineCoord]
    Polyline=arcpy.Polyline(
        arcpy.Array([arcpy.Point(*coords) for coords in lineCoord]))
    return Polyline


#创建一个shp文件
def createShpTable(path,geoType,fields):
    '''
    Fuction:
    Create a shapfile
    Input:
    path---the path of create the new table
    shapetype---- the type of geomentey, eg:'POINT','POLYLINE','POLYGON'
    fields--- is a list, like that [(field1,type),(field2,type),...]
    there are some such field type:'TEXT','FLOAT','DOUBLE','LONG','DATE'
    '''
    out_path = path.replace(path.split('/')[-1],'')
    out_name = path.split('/')[-1]
    arcpy.CreateFeatureclass_management(out_path,out_name,geoType)
    for field in fields:
        arcpy.AddField_management(path,field[0],field[1])


#想shp中插入新数据
def shpInsertData(path,values):
    '''
    Fuction: insert the new data to shp table.
    Input:
    path -- the file of path
    values -- a dict, like that {field1:value1,field2:value2,...} '''
    cursor = arcpy.InsertCursor(path)
    row = cursor.newRow()
    for key in values.keys():
        row.setValue(key,values[key])
    cursor.insertRow(row)
    del cursor, row


#工作空间下是否存在file
def existInEnv(filename,workenv):
    '''
    find the work environment of gdb whether have a file named filename'''
    env = arcpy.Describe(workenv)
    exist = False
    for child in env.children:
        if filename == child.name:
            exist = True
    return exist

#删除重复数据,duplicatefield=['origin_id','destin_id']
def dropDuplicates(inputpath,outpath,duplicatefield):
    df = ReadTable(inputpath)
    print df.shape[0]
    df = df.drop_duplicates(duplicatefield)
    print df.shape[0]
    PandasToShpTemplate(df,outpath,'',inputpath)

#需投影df,目标df,存储文件路径
def createLinkFile(dfProjection,dfTarget,saveFile):
    '''
    Input:
    projection,target: is a dataframe of pandas, and it must have the field of x and y
    '''
    linkdf = pd.DataFrame(columns=['px','py','tx','ty'])
    for index in dfProjection.index:
        linkdf.set_value(index,'px',dfProjection['Shape'][index].centroid.X)
        linkdf.set_value(index,'py',dfProjection['Shape'][index].centroid.Y)
        linkdf.set_value(index,'tx',dfTarget['Shape'][index].centroid.X)
        linkdf.set_value(index,'ty',dfTarget['Shape'][index].centroid.Y)
    linkdf.to_csv(path_or_buf=saveFile,sep='\t',header=False,index=True)
    
