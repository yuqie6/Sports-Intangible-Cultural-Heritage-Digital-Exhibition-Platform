/**
 * @license Copyright (c) 2003-2023, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
    // Define changes to default configuration here
    config.language = 'zh-cn';
    
    // 禁用 PDF 导出功能，消除 exportpdf-no-token-url 警告
    config.removePlugins = 'exportpdf';
    
    // 不依赖缺失的 image2 和 uploadimage 插件
    // config.extraPlugins = 'uploadimage,image2';
    
    // 图片上传相关配置
    config.filebrowserUploadUrl = '/content/upload_image';
    config.uploadUrl = '/content/upload_image';
    config.filebrowserImageUploadUrl = '/content/upload_image';
    config.imageUploadUrl = '/content/upload_image';
    
    // 设置允许上传的图片格式
    config.imageAllowedContent = 'img[alt,src,width,height,data-*]{*}(*);';
    
    // 启用拖放上传图片功能
    config.extraAllowedContent = 'img[alt,src,width,height,data-*]{*}(*);';
    config.imageResize = { maxWidth: 1000, maxHeight: 800 };
    
    // 确保使用绝对路径URL
    config.baseHref = '/';
    
    // 添加自定义处理插件，修复图片URL问题
    config.forceEnterMode = true;
    config.htmlEncodeOutput = false;
    config.entities = false;
    
    // 定义工具栏组
    config.toolbarGroups = [
        { name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
        { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
        { name: 'editing', groups: [ 'find', 'selection', 'spellchecker', 'editing' ] },
        { name: 'forms', groups: [ 'forms' ] },
        '/',
        { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
        { name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi', 'paragraph' ] },
        { name: 'links', groups: [ 'links' ] },
        { name: 'insert', groups: [ 'insert' ] },
        '/',
        { name: 'styles', groups: [ 'styles' ] },
        { name: 'colors', groups: [ 'colors' ] },
        { name: 'tools', groups: [ 'tools' ] },
        { name: 'others', groups: [ 'others' ] },
        { name: 'about', groups: [ 'about' ] }
    ];
    
    // 添加图片上传按钮
    config.toolbar = [
        { name: 'document', items: [ 'Source', '-', 'NewPage', 'Preview', 'Print', '-', 'Templates' ] },
        { name: 'clipboard', items: [ 'Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo' ] },
        { name: 'editing', items: [ 'Find', 'Replace', '-', 'SelectAll', '-', 'Scayt' ] },
        '/',
        { name: 'basicstyles', items: [ 'Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat' ] },
        { name: 'paragraph', items: [ 'NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock' ] },
        { name: 'links', items: [ 'Link', 'Unlink' ] },
        { name: 'insert', items: [ 'Image', 'Table', 'HorizontalRule', 'SpecialChar' ] },
        '/',
        { name: 'styles', items: [ 'Styles', 'Format', 'Font', 'FontSize' ] },
        { name: 'colors', items: [ 'TextColor', 'BGColor' ] },
        { name: 'tools', items: [ 'Maximize'] }
    ];
    
    // 移除一些按钮
    config.removeButtons = 'Save,Preview,Print,Templates,PasteFromWord,Scayt,Form,Checkbox,Radio,TextField,Textarea,Select,Button,ImageButton,HiddenField,CopyFormatting,CreateDiv,BidiLtr,BidiRtl,Language,Anchor,Flash,Iframe,ShowBlocks,About';
};
