cur_frm.cscript.setup = function(doc, cdt, cdn) {
	if(doc.__islocal) {
        console.log('time')
        cur_frm.set_value("checkin_time","");
        cur_frm.set_value("checkout_time","");
        cur_frm.set_value("duration","");
    };
}