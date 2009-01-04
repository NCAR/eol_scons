import os
import SCons
from eol_scons.package import Package
import string

actions = [
    "XERCESCROOT=$XERCESCROOT ./runConfigure -p linux -c gcc -x g++ -m inmem -n socket -t native -r pthread -P $OPT_PREFIX",
    "XERCESCROOT=$XERCESCROOT make",
    "XERCESCROOT=$XERCESCROOT make install"
]

xerces_headers = [] # expanded at end of file

xerces_libs = string.split("""
libxerces-c.so.27
libxerces-c.so.27.0
libxerces-depdom.so.27
libxerces-depdom.so.27.0
""")

class XercescPackage(Package):

    def __init__(self):
        
        headers = [ os.path.join("$OPT_PREFIX","include","xercesc",p) for
                    p in xerces_headers ]
        libs = [ os.path.join("$OPT_PREFIX","lib",p) for
                 p in xerces_libs ]
        Package.__init__(self, "XERCESC",
                         "src/xercesc/runConfigure",
                         actions, libs + headers,
                         default_package_file = "xerces-c-src_2_7_0.tar.gz")
                         
    def setupBuild(self, env):

        env['XERCESCROOT'] = self.getPackagePath(env)
        installs = Package.setupBuild(self, env)
        env.AddGlobalTarget('libxerces-c', installs[0])

    def require(self, env):

        self.checkBuild(env)
        prefix = env['OPT_PREFIX']
        if self.building:
            env['XERCESCROOT'] = self.getPackagePath(env)
            env.Append(LIBS=[env.GetGlobalTarget('libxerces-c'),])
        else:
            env.AppendUnique(LIBPATH=[os.path.join(prefix,'lib'),])
            env.Append(LIBS=['xerces-c'])
            # Supply a hard-coded default for finding doxygen docs
            if not env.has_key('XERCESCROOT'):
                env['XERCESCROOT'] = '/net/src/prog-tools/xerces-c-src_2_6_0'

        if not env.has_key('XERCESC_DOXDIR'):
            env['XERCESC_DOXDIR'] = "%s/doc/html/apiDocs" % env['XERCESCROOT']
        doxref= "xercesc:%s" % env['XERCESC_DOXDIR']
        env.AppendDoxref(doxref)
        env.AppendUnique(CPPPATH=[os.path.join(prefix,'include'),])
        env.Append(DEPLOY_SHARED_LIBS=['xerces-c'])
        

# These are the 2.7 headers.
#
xerces_headers = string.split("""
./parsers/AbstractDOMParser.hpp
./parsers/SAX2XMLFilterImpl.hpp
./parsers/DOMBuilderImpl.hpp
./parsers/XercesDOMParser.hpp
./parsers/SAX2XMLReaderImpl.hpp
./parsers/SAXParser.hpp
./sax2/DeclHandler.hpp
./sax2/ContentHandler.hpp
./sax2/Attributes.hpp
./sax2/XMLReaderFactory.hpp
./sax2/DefaultHandler.hpp
./sax2/LexicalHandler.hpp
./sax2/SAX2XMLReader.hpp
./sax2/SAX2XMLFilter.hpp
./sax/SAXParseException.hpp
./sax/Locator.hpp
./sax/DocumentHandler.hpp
./sax/Parser.hpp
./sax/EntityResolver.hpp
./sax/AttributeList.hpp
./sax/SAXException.hpp
./sax/InputSource.hpp
./sax/DTDHandler.hpp
./sax/HandlerBase.hpp
./sax/ErrorHandler.hpp
./util/XMLAbstractDoubleFloat.hpp
./util/HashXMLCh.hpp
./util/XML88591Transcoder.hpp
./util/CountedPointer.hpp
./util/ValueStackOf.hpp
./util/XercesVersion.hpp
./util/BinInputStream.hpp
./util/ArrayIndexOutOfBoundsException.hpp
./util/KeyRefPair.hpp
./util/KeyValuePair.hpp
./util/BinFileInputStream.hpp
./util/SecurityManager.hpp
./util/regx/UnicodeRangeFactory.hpp
./util/regx/RangeFactory.hpp
./util/regx/Token.hpp
./util/regx/TokenInc.hpp
./util/regx/RegxUtil.hpp
./util/regx/ParserForXMLSchema.hpp
./util/regx/RangeTokenMap.hpp
./util/regx/RangeToken.hpp
./util/regx/Op.hpp
./util/regx/ParenToken.hpp
./util/regx/XMLRangeFactory.hpp
./util/regx/BMPattern.hpp
./util/regx/RegxParser.hpp
./util/regx/ConcatToken.hpp
./util/regx/OpFactory.hpp
./util/regx/RegularExpression.hpp
./util/regx/UniCharTable.hpp
./util/regx/BlockRangeFactory.hpp
./util/regx/CharToken.hpp
./util/regx/ConditionToken.hpp
./util/regx/Match.hpp
./util/regx/TokenFactory.hpp
./util/regx/UnionToken.hpp
./util/regx/ClosureToken.hpp
./util/regx/StringToken.hpp
./util/regx/XMLUniCharacter.hpp
./util/regx/ASCIIRangeFactory.hpp
./util/regx/RegxDefs.hpp
./util/regx/ModifierToken.hpp
./util/IOException.hpp
./util/ParseException.hpp
./util/XMLIBM1140Transcoder.hpp
./util/Janitor.hpp
./util/XMLBigInteger.hpp
./util/UnsupportedEncodingException.hpp
./util/InvalidCastException.hpp
./util/XMLResourceIdentifier.hpp
./util/EncodingValidator.hpp
./util/RefArrayOf.hpp
./util/SchemaDateTimeException.hpp
./util/XMLWin1252Transcoder.hpp
./util/XMLUniDefs.hpp
./util/HashBase.hpp
./util/XMLExceptMsgs.hpp
./util/XML256TableTranscoder.hpp
./util/XMLEntityResolver.hpp
./util/RuntimeException.hpp
./util/XMLUni.hpp
./util/HashCMStateSet.hpp
./util/NumberFormatException.hpp
./util/XMLNumber.hpp
./util/XMLChTranscoder.hpp
./util/XMLDateTime.hpp
./util/FlagJanitor.hpp
./util/HexBin.hpp
./util/PlatformUtils.hpp
./util/XMLEnumerator.hpp
./util/ValueVectorOf.hpp
./util/XMLFloat.hpp
./util/XMLURL.hpp
./util/AutoSense.hpp
./util/NameIdPool.hpp
./util/DefaultPanicHandler.hpp
./util/TransENameMap.hpp
./util/RefHash3KeysIdPool.hpp
./util/XMLMsgLoader.hpp
./util/XMLDeleterFor.hpp
./util/NullPointerException.hpp
./util/XMemory.hpp
./util/NoSuchElementException.hpp
./util/RefHash2KeysTableOf.hpp
./util/Compilers/SunCCDefs.hpp
./util/Compilers/SunKaiDefs.hpp
./util/Compilers/IBMVAOS2Defs.hpp
./util/Compilers/QCCDefs.hpp
./util/Compilers/SCOCCDefs.hpp
./util/Compilers/MVSCPPDefs.hpp
./util/Compilers/HPCCDefs.hpp
./util/Compilers/OS400SetDefs.hpp
./util/Compilers/GCCDefs.hpp
./util/Compilers/IBMVAW32Defs.hpp
./util/Compilers/CodeWarriorDefs.hpp
./util/Compilers/PTXCCDefs.hpp
./util/Compilers/MIPSproDefs.hpp
./util/Compilers/CSetDefs.hpp
./util/Compilers/BorlandCDefs.hpp
./util/Compilers/TandemCCDefs.hpp
./util/Compilers/VCPPDefs.hpp
./util/Compilers/DECCXXDefs.hpp
./util/XMLEBCDICTranscoder.hpp
./util/RefArrayVectorOf.hpp
./util/XMLInteger.hpp
./util/UnexpectedEOFException.hpp
./util/TranscodingException.hpp
./util/XMLHolder.hpp
./util/XMLIBM1047Transcoder.hpp
./util/RefStackOf.hpp
./util/XMLChar.hpp
./util/XMLException.hpp
./util/XMLInitializer.hpp
./util/OutOfMemoryException.hpp
./util/XMLBigDecimal.hpp
./util/XMLUTF16Transcoder.hpp
./util/BinMemInputStream.hpp
./util/TransService.hpp
./util/NetAccessors/Socket/SocketNetAccessor.hpp
./util/NetAccessors/Socket/UnixHTTPURLInputStream.hpp
./util/XMLString.hpp
./util/XMLASCIITranscoder.hpp
./util/XMLUCS4Transcoder.hpp
./util/BaseRefVectorOf.hpp
./util/SynchronizedStringPool.hpp
./util/EmptyStackException.hpp
./util/HashPtr.hpp
./util/MsgLoaders/InMemory/XercesMessages_en_US.hpp
./util/MsgLoaders/InMemory/InMemMsgLoader.hpp
./util/UTFDataFormatException.hpp
./util/QName.hpp
./util/Platforms/Linux/LinuxDefs.hpp
./util/XMLDouble.hpp
./util/Base64.hpp
./util/RefHashTableOf.hpp
./util/PanicHandler.hpp
./util/RefVectorOf.hpp
./util/XMLStringTokenizer.hpp
./util/XercesDefs.hpp
./util/Mutexes.hpp
./util/BitSet.hpp
./util/XMLDOMMsg.hpp
./util/ValueHashTableOf.hpp
./util/StringPool.hpp
./util/XMLNetAccessor.hpp
./util/IllegalArgumentException.hpp
./util/ValueArrayOf.hpp
./util/KVStringPair.hpp
./util/XMLUri.hpp
./util/BitOps.hpp
./util/XMLRegisterCleanup.hpp
./util/Transcoders/Iconv/IconvTransService.hpp
./util/XMLUTF8Transcoder.hpp
./validators/DTD/DTDAttDefList.hpp
./validators/DTD/DTDScanner.hpp
./validators/DTD/DocTypeHandler.hpp
./validators/DTD/XMLDTDDescriptionImpl.hpp
./validators/DTD/DTDAttDef.hpp
./validators/DTD/DTDValidator.hpp
./validators/DTD/DTDEntityDecl.hpp
./validators/DTD/DTDGrammar.hpp
./validators/DTD/DTDElementDecl.hpp
./validators/schema/XercesGroupInfo.hpp
./validators/schema/XSDErrorReporter.hpp
./validators/schema/SubstitutionGroupComparator.hpp
./validators/schema/XercesElementWildcard.hpp
./validators/schema/SchemaElementDecl.hpp
./validators/schema/XSDLocator.hpp
./validators/schema/TraverseSchema.hpp
./validators/schema/NamespaceScope.hpp
./validators/schema/XercesAttGroupInfo.hpp
./validators/schema/SchemaValidator.hpp
./validators/schema/XMLSchemaDescriptionImpl.hpp
./validators/schema/identity/ValueStoreCache.hpp
./validators/schema/identity/FieldActivator.hpp
./validators/schema/identity/IC_Key.hpp
./validators/schema/identity/XPathMatcherStack.hpp
./validators/schema/identity/XPathException.hpp
./validators/schema/identity/IdentityConstraintHandler.hpp
./validators/schema/identity/IC_Field.hpp
./validators/schema/identity/FieldValueMap.hpp
./validators/schema/identity/XPathMatcher.hpp
./validators/schema/identity/XercesXPath.hpp
./validators/schema/identity/ValueStore.hpp
./validators/schema/identity/IC_KeyRef.hpp
./validators/schema/identity/IC_Unique.hpp
./validators/schema/identity/XPathSymbols.hpp
./validators/schema/identity/IdentityConstraint.hpp
./validators/schema/identity/IC_Selector.hpp
./validators/schema/SchemaGrammar.hpp
./validators/schema/GeneralAttributeCheck.hpp
./validators/schema/SchemaSymbols.hpp
./validators/schema/PSVIDefs.hpp
./validators/schema/SchemaInfo.hpp
./validators/schema/XSDDOMParser.hpp
./validators/schema/XUtil.hpp
./validators/schema/ComplexTypeInfo.hpp
./validators/schema/SchemaAttDef.hpp
./validators/schema/SchemaAttDefList.hpp
./validators/common/CMAny.hpp
./validators/common/CMBinaryOp.hpp
./validators/common/CMStateSet.hpp
./validators/common/ContentSpecNode.hpp
./validators/common/CMLeaf.hpp
./validators/common/CMNode.hpp
./validators/common/AllContentModel.hpp
./validators/common/SimpleContentModel.hpp
./validators/common/GrammarResolver.hpp
./validators/common/Grammar.hpp
./validators/common/MixedContentModel.hpp
./validators/common/DFAContentModel.hpp
./validators/common/CMUnaryOp.hpp
./validators/common/ContentLeafNameTypeVector.hpp
./validators/datatype/NOTATIONDatatypeValidator.hpp
./validators/datatype/AbstractNumericFacetValidator.hpp
./validators/datatype/YearMonthDatatypeValidator.hpp
./validators/datatype/TimeDatatypeValidator.hpp
./validators/datatype/DateTimeValidator.hpp
./validators/datatype/InvalidDatatypeValueException.hpp
./validators/datatype/BooleanDatatypeValidator.hpp
./validators/datatype/StringDatatypeValidator.hpp
./validators/datatype/DoubleDatatypeValidator.hpp
./validators/datatype/DatatypeValidator.hpp
./validators/datatype/NCNameDatatypeValidator.hpp
./validators/datatype/DurationDatatypeValidator.hpp
./validators/datatype/YearDatatypeValidator.hpp
./validators/datatype/MonthDatatypeValidator.hpp
./validators/datatype/DateDatatypeValidator.hpp
./validators/datatype/DatatypeValidatorFactory.hpp
./validators/datatype/AbstractStringValidator.hpp
./validators/datatype/DayDatatypeValidator.hpp
./validators/datatype/XMLCanRepGroup.hpp
./validators/datatype/ENTITYDatatypeValidator.hpp
./validators/datatype/HexBinaryDatatypeValidator.hpp
./validators/datatype/AbstractNumericValidator.hpp
./validators/datatype/FloatDatatypeValidator.hpp
./validators/datatype/InvalidDatatypeFacetException.hpp
./validators/datatype/AnySimpleTypeDatatypeValidator.hpp
./validators/datatype/UnionDatatypeValidator.hpp
./validators/datatype/ListDatatypeValidator.hpp
./validators/datatype/AnyURIDatatypeValidator.hpp
./validators/datatype/Base64BinaryDatatypeValidator.hpp
./validators/datatype/IDDatatypeValidator.hpp
./validators/datatype/NameDatatypeValidator.hpp
./validators/datatype/QNameDatatypeValidator.hpp
./validators/datatype/DateTimeDatatypeValidator.hpp
./validators/datatype/IDREFDatatypeValidator.hpp
./validators/datatype/MonthDayDatatypeValidator.hpp
./validators/datatype/DecimalDatatypeValidator.hpp
./dom/DOMWriterFilter.hpp
./dom/DOMDocumentType.hpp
./dom/DOMPSVITypeInfo.hpp
./dom/DOMProcessingInstruction.hpp
./dom/DOMEntity.hpp
./dom/DOMRangeException.hpp
./dom/DOMText.hpp
./dom/DOMRange.hpp
./dom/DOM.hpp
./dom/DOMErrorHandler.hpp
./dom/DOMXPathResult.hpp
./dom/DOMNodeFilter.hpp
./dom/DOMImplementationSource.hpp
./dom/DOMImplementation.hpp
./dom/DOMDocumentRange.hpp
./dom/DOMBuilder.hpp
./dom/DOMComment.hpp
./dom/DOMNotation.hpp
./dom/DOMLocator.hpp
./dom/DOMNamedNodeMap.hpp
./dom/DOMInputSource.hpp
./dom/DOMNodeIterator.hpp
./dom/DOMCharacterData.hpp
./dom/DOMException.hpp
./dom/DOMImplementationLS.hpp
./dom/deprecated/DOM_DocumentFragment.hpp
./dom/deprecated/DOM_TreeWalker.hpp
./dom/deprecated/DOM_Text.hpp
./dom/deprecated/DOM_ProcessingInstruction.hpp
./dom/deprecated/DOM_DOMException.hpp
./dom/deprecated/DOMParser.hpp
./dom/deprecated/DOM.hpp
./dom/deprecated/DOM_NodeIterator.hpp
./dom/deprecated/DOM_NamedNodeMap.hpp
./dom/deprecated/DOM_Comment.hpp
./dom/deprecated/DOM_Notation.hpp
./dom/deprecated/DOM_CharacterData.hpp
./dom/deprecated/DOM_RangeException.hpp
./dom/deprecated/DOM_DOMImplementation.hpp
./dom/deprecated/DOM_Range.hpp
./dom/deprecated/DOM_Entity.hpp
./dom/deprecated/DOM_Element.hpp
./dom/deprecated/DOM_Node.hpp
./dom/deprecated/DOM_Attr.hpp
./dom/deprecated/DOM_NodeList.hpp
./dom/deprecated/DOM_DocumentType.hpp
./dom/deprecated/DOM_NodeFilter.hpp
./dom/deprecated/DOM_CDATASection.hpp
./dom/deprecated/DomMemDebug.hpp
./dom/deprecated/DOMString.hpp
./dom/deprecated/DOM_EntityReference.hpp
./dom/deprecated/DOM_Document.hpp
./dom/deprecated/DOM_XMLDecl.hpp
./dom/DOMNode.hpp
./dom/DOMXPathNamespace.hpp
./dom/DOMConfiguration.hpp
./dom/DOMNodeList.hpp
./dom/StDOMNode.hpp
./dom/DOMImplementationRegistry.hpp
./dom/DOMError.hpp
./dom/DOMXPathEvaluator.hpp
./dom/DOMAttr.hpp
./dom/DOMXPathExpression.hpp
./dom/DOMEntityReference.hpp
./dom/DOMXPathException.hpp
./dom/DOMDocument.hpp
./dom/DOMElement.hpp
./dom/DOMTypeInfo.hpp
./dom/DOMDocumentTraversal.hpp
./dom/DOMEntityResolver.hpp
./dom/DOMWriter.hpp
./dom/DOMXPathNSResolver.hpp
./dom/DOMDocumentFragment.hpp
./dom/DOMTreeWalker.hpp
./dom/DOMUserDataHandler.hpp
./dom/DOMCDATASection.hpp
./internal/EndOfEntityException.hpp
./internal/IGXMLScanner.hpp
./internal/ValidationContextImpl.hpp
./internal/XSerializationException.hpp
./internal/XProtoType.hpp
./internal/CharTypeTables.hpp
./internal/BinFileOutputStream.hpp
./internal/MemoryManagerImpl.hpp
./internal/XSAXMLScanner.hpp
./internal/XMLGrammarPoolImpl.hpp
./internal/XMLInternalErrorHandler.hpp
./internal/VecAttrListImpl.hpp
./internal/SGXMLScanner.hpp
./internal/BinMemOutputStream.hpp
./internal/WFXMLScanner.hpp
./internal/IANAEncodings.hpp
./internal/XSerializable.hpp
./internal/XTemplateSerializer.hpp
./internal/ReaderMgr.hpp
./internal/VecAttributesImpl.hpp
./internal/DGXMLScanner.hpp
./internal/XMLReader.hpp
./internal/XMLScannerResolver.hpp
./internal/XSObjectFactory.hpp
./internal/XMLScanner.hpp
./internal/ElemStack.hpp
./internal/MemoryManagerArrayImpl.hpp
./internal/XSerializeEngine.hpp
./framework/psvi/XSModel.hpp
./framework/psvi/XSObject.hpp
./framework/psvi/XSConstants.hpp
./framework/psvi/XSParticle.hpp
./framework/psvi/XSAttributeGroupDefinition.hpp
./framework/psvi/XSFacet.hpp
./framework/psvi/PSVIAttribute.hpp
./framework/psvi/XSIDCDefinition.hpp
./framework/psvi/XSAnnotation.hpp
./framework/psvi/XSNamedMap.hpp
./framework/psvi/XSMultiValueFacet.hpp
./framework/psvi/XSModelGroupDefinition.hpp
./framework/psvi/XSValue.hpp
./framework/psvi/PSVIItem.hpp
./framework/psvi/XSNamespaceItem.hpp
./framework/psvi/XSElementDeclaration.hpp
./framework/psvi/XSTypeDefinition.hpp
./framework/psvi/PSVIHandler.hpp
./framework/psvi/XSWildcard.hpp
./framework/psvi/XSNotationDeclaration.hpp
./framework/psvi/XSAttributeDeclaration.hpp
./framework/psvi/XSComplexTypeDefinition.hpp
./framework/psvi/XSAttributeUse.hpp
./framework/psvi/XSSimpleTypeDefinition.hpp
./framework/psvi/XSModelGroup.hpp
./framework/psvi/PSVIElement.hpp
./framework/psvi/PSVIAttributeList.hpp
./framework/StdOutFormatTarget.hpp
./framework/XMLBuffer.hpp
./framework/Wrapper4DOMInputSource.hpp
./framework/XMLBufferMgr.hpp
./framework/XMLErrorCodes.hpp
./framework/XMLContentModel.hpp
./framework/MemBufFormatTarget.hpp
./framework/XMLEntityDecl.hpp
./framework/XMLValidityCodes.hpp
./framework/XMLGrammarDescription.hpp
./framework/XMLFormatter.hpp
./framework/XMLGrammarPool.hpp
./framework/XMLErrorReporter.hpp
./framework/XMLDTDDescription.hpp
./framework/URLInputSource.hpp
./framework/MemoryManager.hpp
./framework/XMLAttr.hpp
./framework/XMLAttDef.hpp
./framework/XMLDocumentHandler.hpp
./framework/XMLRecognizer.hpp
./framework/XMLAttDefList.hpp
./framework/ValidationContext.hpp
./framework/BinOutputStream.hpp
./framework/LocalFileFormatTarget.hpp
./framework/XMLNotationDecl.hpp
./framework/XMLSchemaDescription.hpp
./framework/XMLValidator.hpp
./framework/MemBufInputSource.hpp
./framework/XMLRefInfo.hpp
./framework/LocalFileInputSource.hpp
./framework/XMLPScanToken.hpp
./framework/XMLElementDecl.hpp
./framework/XMLEntityHandler.hpp
./framework/StdInInputSource.hpp
./framework/Wrapper4InputSource.hpp
""")


xercesc = XercescPackage()

def generate(env):
    xercesc.require(env)



def exists(env):
    return True

