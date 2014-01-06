<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0"
                xmlns:exsl="http://exslt.org/common"
                extension-element-prefixes="exsl">
  <xsl:template match="DjVuXML/BODY/OBJECT">
    <exsl:document href="{@usemap}" indent="yes" encoding="UTF-8" >
      <OBJECT>
        <PARAM name="PAGE" value="{translate(@usemap,'.djvu','.xml')}"/>
        <xsl:for-each select="HIDDENTEXT/PAGECOLUMN/REGION/PARAGRAPH/LINE">
          <LINE>
            <xsl:for-each select=".//WORD">
              <xsl:if test="not(position() = 1)">
                <xsl:text> </xsl:text>
              </xsl:if>
              <xsl:value-of select="text()"/>
            </xsl:for-each>
          </LINE>
        </xsl:for-each>
      </OBJECT>
    </exsl:document>
  </xsl:template>
</xsl:stylesheet>
