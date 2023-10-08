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
                    <xsl:text>INT(</xsl:text>

                    <xsl:choose>
                        <xsl:when test="xs:simpleType/xs:restriction/xs:totalDigits/@value">
                            <xsl:value-of select="xs:simpleType/xs:restriction/xs:totalDigits/@value" />
                        </xsl:when>
                        <xsl:otherwise>
                             <xsl:text>11</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>

                    <xsl:text>)</xsl:text>
                </xsl:when>
                <xsl:when test="xs:simpleType/xs:restriction/@base='xs:byte'">INT(1)</xsl:when>
                <xsl:when test="xs:simpleType/xs:restriction/@base='xs:string'">
                    <xsl:choose>
                        <xsl:when test="xs:simpleType/xs:restriction/xs:maxLength">
                            <xsl:call-template name="type-string">
                                <xsl:with-param name="length" select="xs:simpleType/xs:restriction/xs:maxLength/@value" />
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="xs:simpleType/xs:restriction/xs:length">
                            <xsl:call-template name="type-string">
                                <xsl:with-param name="length" select="xs:simpleType/xs:restriction/xs:length/@value" />
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="type-string">
                                <xsl:with-param name="length" select="128" />
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="xs:simpleType/xs:restriction/@base='xs:date'">DATE</xsl:when>
                <xsl:when test="@type='xs:date'">DATE</xsl:when>
                <xsl:when test="@type='xs:boolean'">INT(1)</xsl:when>
                <xsl:when test="@type='xs:integer'">INT</xsl:when>
                <xsl:when test="@type='xs:long'">INT</xsl:when>
                <xsl:otherwise>VARCHAR(128)</xsl:otherwise>
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
        <xsl:text>&#xa;) ENGINE = MyISAM </xsl:text>

        <!-- Table comment -->
        <xsl:if test="/xs:schema/xs:element[1]/xs:annotation/xs:documentation">
            <xsl:text>COMMENT=</xsl:text>
            <xsl:text>'</xsl:text><xsl:value-of select="/xs:schema/xs:element[1]/xs:annotation/xs:documentation"/><xsl:text>'</xsl:text>
        </xsl:if>

        <xsl:text>; &#xa;</xsl:text>

        <!-- separate table definitions -->
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template name="type-string">
        <xsl:param name="length"/>
        <xsl:choose>
            <xsl:when test="$length > 255">
                <xsl:text>TEXT</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>VARCHAR(</xsl:text><xsl:value-of select="$length" /><xsl:text>)</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>