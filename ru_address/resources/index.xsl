<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" encoding="UTF-8"/>

    <!-- From XSLT processor -->
    <xsl:param name="table_name" />

    <xsl:template match="/">
    	<xsl:for-each select="/database/table[@id=$table_name]">
    		<xsl:call-template name="create_index"/>
    	</xsl:for-each>
    </xsl:template>
    

	<xsl:template name="create_index">
		<!-- <xsl:text>ALTER TABLE `</xsl:text><xsl:value-of select="@id"/><xsl:text>`</xsl:text> -->

		<!-- For each key, handle key type in loop -->
		<xsl:for-each select="*">
		
			<xsl:choose>
				<xsl:when test="name(current()) = 'primary-key'">
					<xsl:text>PRIMARY KEY (`</xsl:text><xsl:value-of select="@field"/><xsl:text>`)</xsl:text>
				</xsl:when>
				<xsl:when test="name(current()) = 'foreign-key'">
					<xsl:text>FOREIGN KEY (`</xsl:text><xsl:value-of select="@field"/><xsl:text>`)</xsl:text>
					<xsl:text> REFERENCES `</xsl:text><xsl:value-of select="@for-table"/><xsl:text>` (`</xsl:text><xsl:value-of select="@for-field"/><xsl:text>`)</xsl:text>
				</xsl:when>
				<xsl:when test="name(current()) = 'key'">
					<xsl:text>INDEX `</xsl:text><xsl:value-of select="@field"/><xsl:text>` (`</xsl:text><xsl:value-of select="@field"/><xsl:text>`)</xsl:text>
				</xsl:when>
			</xsl:choose>
			
			<!-- Separator -->
			<xsl:if test="position() != last()">
				<xsl:text>,&#xa;  </xsl:text>
			</xsl:if>
		
		</xsl:for-each>

		<xsl:if test="position() != last()">
			<xsl:text>&#xa;</xsl:text>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>