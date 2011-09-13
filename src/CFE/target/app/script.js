Ext.onReady(function() {

    function onSaveBtnClick(item){
		conn.request({
			url: 'writefile.cgi',
			params: Ext.urlEncode({name: combo.value, action: texta.getValue()}),
			success: function(responseObject) {
				if (responseObject.responseText=="ok\n") {
					Ext.Msg.alert('Status','Changes saved.');
				} else {
					Ext.Msg.alert('Status',responseObject.responseText);
				}

				saveBtn.disable();
				repairBtn.enable();
			}
		});
	}
	
	
    function onRepairBtnClick(item){
		if (!(saveBtn.disabled)) {
			Ext.MessageBox.show({
				title: 'Warning',
				msg: 'Unsaved changes, are you sure you want to load original file?',
				icon: Ext.MessageBox.WARNING,
				buttons: Ext.MessageBox.YESNOCANCEL,
				fn: function(btn, text) {
					if (btn=='yes') {
						conn.request({
							url: 'getfile.cgi?'+Ext.urlEncode({action: combo.value})+'.original',
							success: function(responseObject) {
								texta.setValue(responseObject.responseText);
							}
						});
						repairBtn.enable();
						saveBtn.enable();
					}
				}
			})
		} else {
			conn.request({
				url: 'getfile.cgi?'+Ext.urlEncode({action: combo.value})+'.original',
				success: function(responseObject) {
					texta.setValue(responseObject.responseText);
				}
			});
			repairBtn.enable();
			saveBtn.enable();
		}

	}

	var conn = new Ext.data.Connection();

    function onComboClick(item){
		conn.request({
			url: 'getfile.cgi?'+Ext.urlEncode({action: combo.value}),
			success: function(responseObject) {
				texta.setValue(responseObject.responseText);
			}
		});
		repairBtn.enable();
		saveBtn.disable();
	}


	var texta = new Ext.form.TextArea ({
		hideLabel: true,
		name: 'msg',
		style: 'font-family:monospace',
		anchor: '100% -53',
		enableKeyEvents:true,
		listeners: {
			keypress: function(f, e) {
				if (saveBtn.disabled) {
					saveBtn.enable();
				}
			}
		}

	});


	var combo = new Ext.form.ComboBox ({
		store: [==:names:==],
		name: 'file',
		shadow: true,
		editable: false,
		mode: 'local',
		triggerAction: 'all',
		emptyText: 'Choose config file',
		selectOnFocus: true
	});

	var saveBtn = new Ext.Toolbar.Button({
		handler: onSaveBtnClick,
		name: 'save',
		text: 'Save',
		cls: 'x-btn-text-icon',
		icon: '/webman/images/toolbar_save.png',
		disabled: true
	});

	var repairBtn = new Ext.Toolbar.Button({
		handler: onRepairBtnClick,
		name: 'original',
		text: 'Original',
		cls: 'x-btn-text-icon',
		icon: '/webman/images/toolbar_repair.png',
		disabled: true
	});


    var form = new Ext.form.FormPanel({
        baseCls: 'x-plain',
        url:'save-form.php',
        items: [
			new Ext.Toolbar({
				items: [
					'-',
					saveBtn,
					'-',
					repairBtn,
					'-',
					combo
				]
			}),
			texta
		]
    });

	combo.addListener('select',onComboClick);

    var window = new Ext.Window({
        title: 'Config File Editor',
        width: 800,
        height:500,
        minWidth: 300,
        minHeight: 200,
		x:10, y:60,
        layout: 'fit',
        plain:true,
        bodyStyle:'padding:5px;',
		items: form
    });

    window.show();
});
