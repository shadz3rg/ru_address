<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" encoding="UTF-8"/>
    
    <!-- From XSLT processor -->
    <xsl:param name="table_name" />
    <xsl:param name="index" />
    
    <xsl:template match="/">
        <xsl:text>DROP TABLE IF EXISTS `</xsl:text><xsl:value-of select="$table_name"/><xsl:text>`;&#xa;</xsl:text>
        <xsl:text>CREATE TABLE `</xsl:text><xsl:value-of select="$table_name"/><xsl:text>` (&#xa;</xsl:text>
        <xsl:for-each select=".//xs:complexType[1]/xs:attribute" >
            <!-- Column -->
            <xsl:text>  `</xsl:text><xsl:value-of select="normalize-space(@name)"/><xsl:text>` </xsl:text>

            <!-- Column Type -->
            <xsl:choose>
                 <xsl:when test="xs:simpleType/xs:restriction/@base='xs:integer' or xs:simpleType/xs:restriction/@base='xs:int' or xs:simpleType/xs:restriction/@base='xs:long'">
                    <xsl:choose>
                        <xsl:when test="xs:simpleType/xs:restriction/xs:totalDigits/@value='5'">
                             <xsl:text>Int16</xsl:text>
                        </xsl:when>
                        <xsl:when test="xs:simpleType/xs:restriction/xs:totalDigits/@value='10'">
                             <xsl:text>Int32</xsl:text>
                        </xsl:when>
                        <xsl:when test="xs:simpleType/xs:restriction/xs:totalDigits/@value='19'">
                             <xsl:text>Int64</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                             <xsl:text>Int32</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="xs:simpleType/xs:restriction/@base='xs:byte'">Int8</xsl:when>
                <xsl:when test="xs:simpleType/xs:restriction/@base='xs:string'">String</xsl:when>
                <xsl:when test="xs:simpleType/xs:restriction/@base='xs:date'">Date</xsl:when>
                <xsl:when test="@type='xs:date'">Date</xsl:when>
                <xsl:when test="@type='xs:boolean'">Bool</xsl:when>
                <xsl:when test="@type='xs:integer'">Int32</xsl:when>
                <xsl:when test="@type='xs:long'">Int64</xsl:when>
                <xsl:otherwise>String</xsl:otherwise>
            </xsl:choose>

            <!-- Column required -->
            <xsl:choose>
                <xsl:when test="@use='required'">
                    <xsl:text> NOT NULL</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text> NULL DEFAULT NULL</xsl:text>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Column comment -->
            <xsl:if test="xs:annotation/xs:documentation">
                <xsl:text> COMMENT </xsl:text>
                <xsl:choose>
                    <xsl:when test="contains(xs:annotation/xs:documentation,'&#xa;')">
                        <xsl:text>'</xsl:text><xsl:value-of select="substring-before(xs:annotation/xs:documentation,'&#xa;')"/><xsl:text>'</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>'</xsl:text><xsl:value-of select="xs:annotation/xs:documentation"/><xsl:text>'</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>

            <!-- Columns separator -->
            <xsl:choose>
                <xsl:when test="position()!=last()">,&#xa;</xsl:when>
                <xsl:otherwise>
                    <xsl:if test="$index !=''">,&#xa;  <xsl:value-of select="$index"/></xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>

        <!-- End of column definitions -->
        <xsl:text>&#xa;) ENGINE = MergeTree </xsl:text>

        <!-- Table comment -->
        <xsl:if test="/xs:schema/xs:element[1]/xs:annotation/xs:documentation">
            <xsl:text>COMMENT </xsl:text>
            <xsl:text>'</xsl:text><xsl:value-of select="/xs:schema/xs:element[1]/xs:annotation/xs:documentation"/><xsl:text>'</xsl:text>
        </xsl:if>

        <xsl:text>; &#xa;</xsl:text>

        <!-- separate table definitions -->
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>
</xsl:stylesheet>